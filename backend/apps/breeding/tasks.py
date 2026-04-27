"""
Breeding Celery Tasks
=====================
Phase 4: Breeding & Genetics Engine

Async tasks for closure table rebuild and maintenance.
"""

import logging
from typing import Optional
from uuid import UUID

from celery import shared_task
from django.db import connection

from apps.breeding.models import DogClosure
from apps.operations.models import Dog

logger = logging.getLogger(__name__)


@shared_task(queue="low", bind=True, max_retries=2)
def rebuild_closure_table(self, full_rebuild: bool = True, dog_id: Optional[str] = None):
    """
    Rebuild the pedigree closure table.

    The closure table stores all ancestor-descendant paths for efficient
    COI calculation. This task is called:
    - After bulk CSV imports (full_rebuild=True)
    - After new litter records (full_rebuild=False, dog_id=dam_id)

    Args:
        full_rebuild: If True, truncate and rebuild entire table.
                      If False, only update paths for specific dog.
        dog_id: UUID of dog to update (only used if full_rebuild=False)

    Returns:
        Dict with status, duration, and record counts
    """
    import time
    start_time = time.time()

    try:
        if full_rebuild:
            # Full rebuild - clear table and rebuild all paths
            with connection.cursor() as cursor:
                # Truncate existing data
                cursor.execute("TRUNCATE dog_closure RESTART IDENTITY;")

                # Insert all ancestor paths using recursive CTE
                cursor.execute("""
                    INSERT INTO dog_closure (id, ancestor_id, descendant_id, depth, entity_id, created_at)
                    WITH RECURSIVE pedigree_paths AS (
                        -- Base case: each dog is its own ancestor at depth 0
                        SELECT
                            gen_random_uuid() as id,
                            d.id as ancestor_id,
                            d.id as descendant_id,
                            0 as depth,
                            d.entity_id,
                            NOW() as created_at
                        FROM dogs d
                        WHERE d.dam_id IS NOT NULL OR d.sire_id IS NOT NULL

                        UNION ALL

                        -- Recursive case: traverse up the pedigree
                        SELECT
                            gen_random_uuid(),
                            COALESCE(parent.dam_id, parent.sire_id) as ancestor_id,
                            pp.descendant_id,
                            pp.depth + 1,
                            parent.entity_id,
                            NOW()
                        FROM pedigree_paths pp
                        JOIN dogs parent ON parent.id = pp.ancestor_id
                        WHERE pp.depth < 10
                          AND (parent.dam_id IS NOT NULL OR parent.sire_id IS NOT NULL)
                    )
                    SELECT id, ancestor_id, descendant_id, depth, entity_id, created_at
                    FROM pedigree_paths
                    WHERE ancestor_id IS NOT NULL
                      AND depth > 0
                """)

            duration_ms = int((time.time() - start_time) * 1000)
            count = DogClosure.objects.count()

            logger.info(f"Full closure table rebuild completed in {duration_ms}ms ({count} records)")

            return {
                "status": "closure_rebuilt",
                "full": True,
                "duration_ms": duration_ms,
                "record_count": count,
            }

        else:
            # Incremental update for single dog
            if not dog_id:
                raise ValueError("dog_id required for incremental rebuild")

            dog_uuid = UUID(dog_id)

            # Remove existing paths for this dog
            DogClosure.objects.filter(descendant_id=dog_uuid).delete()

            # Insert new paths
            with connection.cursor() as cursor:
                cursor.execute("""
                    WITH RECURSIVE pedigree_paths AS (
                        -- Base case
                        SELECT
                            d.id as ancestor_id,
                            d.id as descendant_id,
                            0 as depth,
                            d.entity_id
                        FROM dogs d
                        WHERE d.id = %s

                        UNION ALL

                        -- Recursive case
                        SELECT
                            COALESCE(parent.dam_id, parent.sire_id),
                            pp.descendant_id,
                            pp.depth + 1,
                            parent.entity_id
                        FROM pedigree_paths pp
                        JOIN dogs parent ON parent.id = pp.ancestor_id
                        WHERE pp.depth < 10
                          AND (parent.dam_id IS NOT NULL OR parent.sire_id IS NOT NULL)
                    )
                    INSERT INTO dog_closure (id, ancestor_id, descendant_id, depth, entity_id, created_at)
                    SELECT gen_random_uuid(), ancestor_id, descendant_id, depth, entity_id, NOW()
                    FROM pedigree_paths
                    WHERE ancestor_id IS NOT NULL
                      AND depth > 0
                """, [dog_uuid])

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Incremental closure rebuild for dog {dog_id} completed in {duration_ms}ms")

            return {
                "status": "closure_rebuilt",
                "full": False,
                "dog_id": dog_id,
                "duration_ms": duration_ms,
            }

    except Exception as exc:
        logger.error(f"Closure table rebuild failed: {exc}")
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task(queue="low")
def trigger_closure_rebuild(full_rebuild: bool = False, dog_id: Optional[str] = None):
    """
    Trigger closure table rebuild via Celery.

    This is a wrapper task that can be called synchronously
    or chained with other tasks.
    """
    return rebuild_closure_table.delay(full_rebuild=full_rebuild, dog_id=dog_id)


@shared_task(queue="low")
def verify_closure_integrity():
    """
    Verify closure table integrity and report any issues.

    Runs as a periodic task to ensure data consistency.
    """
    issues = []

    # Check for orphaned records (descendants that don't exist)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM dog_closure dc
            LEFT JOIN dogs d ON d.id = dc.descendant_id
            WHERE d.id IS NULL
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned:
            issues.append(f"{orphaned} orphaned descendant records")

    # Check for missing paths (dogs without closure entries)
        cursor.execute("""
            SELECT COUNT(*)
            FROM dogs d
            LEFT JOIN dog_closure dc ON dc.descendant_id = d.id
            WHERE d.dam_id IS NOT NULL OR d.sire_id IS NOT NULL
              AND dc.id IS NULL
        """)
        missing = cursor.fetchone()[0]
        if missing:
            issues.append(f"{missing} dogs missing closure paths")

    if issues:
        logger.warning(f"Closure integrity issues found: {', '.join(issues)}")
        return {"status": "issues_found", "issues": issues}

    logger.info("Closure table integrity verified - no issues found")
    return {"status": "ok", "issues": []}


@shared_task(queue="default")
def invalidate_coi_cache_for_dog(dog_id: str):
    """
    Invalidate COI cache for all pairings involving a specific dog.

    Called when pedigree data changes (e.g., dam/sire corrections).
    """
    from django.core.cache import cache

    # Find all COI cache keys for this dog
    pattern = f"coi:*:{dog_id}:*"
    keys = cache.keys(pattern)

    pattern2 = f"coi:{dog_id}:*"
    keys2 = cache.keys(pattern2)

    all_keys = set(keys + keys2)

    # Delete all matching keys
    for key in all_keys:
        cache.delete(key)

    logger.info(f"Invalidated {len(all_keys)} COI cache entries for dog {dog_id}")

    return {"invalidated_count": len(all_keys)}
