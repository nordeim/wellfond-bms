"""
COI (Coefficient of Inbreeding) Calculator
========================================
Phase 4: Breeding & Genetics Engine

Implements Wright's formula for calculating COI:
COI = Σ[(0.5)^(n1 + n2 + 1) * (1 + Fa)]

Where:
- n1 = generations from dam to common ancestor
- n2 = generations from sire to common ancestor
- Fa = COI of the common ancestor (0 if unknown)

Uses the closure table for efficient ancestor traversal.
"""

import logging
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from django.core.cache import cache
from django.db import connection

from apps.breeding.models import DogClosure
from apps.operations.models import Dog

logger = logging.getLogger(__name__)

# Cache TTL for COI calculations (1 hour)
COI_CACHE_TTL = 3600


def get_cache_key(dam_id: UUID, sire_id: UUID, generations: int = 5) -> str:
    """Generate cache key for COI calculation."""
    return f"coi:{dam_id}:{sire_id}:{generations}"


def get_shared_ancestors(
    dam_id: UUID,
    sire_id: UUID,
    generations: int = 5
) -> List[dict]:
    """
    Find all common ancestors between two dogs using the closure table.

    Args:
        dam_id: UUID of the dam (female)
        sire_id: UUID of the sire (male)
        generations: Maximum generations to search (default: 5)

    Returns:
        List of dicts with ancestor info, including:
        - dog_id: UUID of the common ancestor
        - name: Name of the ancestor
        - microchip: Microchip number
        - depth_dam: Generations from dam to ancestor
        - depth_sire: Generations from sire to ancestor
        - total_depth: Sum of both depths
    """
    with connection.cursor() as cursor:
        # SQL query using closure table
        # Find all ancestors of dam and sire, then find intersections
        cursor.execute("""
            WITH dam_ancestors AS (
                SELECT ancestor_id, depth
                FROM dog_closure
                WHERE descendant_id = %s AND depth <= %s
                UNION
                SELECT %s::uuid as ancestor_id, 0 as depth
            ),
            sire_ancestors AS (
                SELECT ancestor_id, depth
                FROM dog_closure
                WHERE descendant_id = %s AND depth <= %s
                UNION
                SELECT %s::uuid as ancestor_id, 0 as depth
            )
            SELECT
                d.id as dog_id,
                d.name,
                d.microchip,
                da.depth as depth_dam,
                sa.depth as depth_sire
            FROM dam_ancestors da
            JOIN sire_ancestors sa ON da.ancestor_id = sa.ancestor_id
            JOIN dogs d ON d.id = da.ancestor_id
            WHERE da.ancestor_id != %s AND da.ancestor_id != %s
            ORDER BY (da.depth + sa.depth), d.name
        """, [dam_id, generations, dam_id, sire_id, generations, sire_id, dam_id, sire_id])

        ancestors = []
        for row in cursor.fetchall():
            dog_id, name, microchip, depth_dam, depth_sire = row
            ancestors.append({
                "dog_id": dog_id,
                "name": name,
                "microchip": microchip,
                "depth_dam": depth_dam,
                "depth_sire": depth_sire,
                "total_depth": depth_dam + depth_sire,
            })

    return ancestors


def calc_coi(
    dam_id: UUID,
    sire_id: UUID,
    generations: int = 5,
    use_cache: bool = True
) -> dict:
    """
    Calculate Coefficient of Inbreeding using Wright's formula.

    Wright's formula: COI = Σ[(0.5)^(n1 + n2 + 1) * (1 + Fa)]

    Args:
        dam_id: UUID of the dam (female)
        sire_id: UUID of the sire (male)
        generations: Maximum generations to analyze (default: 5)
        use_cache: Whether to use Redis cache (default: True)

    Returns:
        Dict with:
        - coi_pct: COI as percentage (0-100)
        - shared_ancestors: List of common ancestors with details
        - generation_depth: Number of generations analyzed
        - cached: Whether result was from cache
    """
    # Check cache if enabled
    cache_key = get_cache_key(dam_id, sire_id, generations)
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            cached_result["cached"] = True
            logger.debug(f"COI cache hit for {dam_id} x {sire_id}")
            return cached_result

    # Get shared ancestors
    ancestors = get_shared_ancestors(dam_id, sire_id, generations)

    if not ancestors:
        # No common ancestors - COI = 0
        result = {
            "coi_pct": 0.0,
            "shared_ancestors": [],
            "generation_depth": generations,
            "cached": False,
        }
        if use_cache:
            cache.set(cache_key, result, COI_CACHE_TTL)
        return result

    # Calculate COI using Wright's formula
    coi = Decimal("0.0")
    ancestor_details = []

    for ancestor in ancestors:
        n1 = ancestor["depth_dam"]
        n2 = ancestor["depth_sire"]

        # Wright's formula: (0.5)^(n1 + n2 + 1)
        contribution = Decimal("0.5") ** (n1 + n2 + 1)

        # Note: Fa (ancestor's own COI) is typically 0 for unknown
        # For purebred lines with known COI, this could be fetched from cache
        fa = Decimal("0.0")  # Assume 0 if not known

        # Full formula: (0.5)^(n1+n2+1) * (1 + Fa)
        contribution = contribution * (Decimal("1.0") + fa)

        coi += contribution

        # Build ancestor detail for response
        relationship = _get_relationship_name(n1, n2)
        ancestor_details.append({
            "dog_id": ancestor["dog_id"],
            "name": ancestor["name"],
            "microchip": ancestor["microchip"],
            "relationship": relationship,
            "generations_back": max(n1, n2),
            "depth_dam": n1,
            "depth_sire": n2,
            "contribution_pct": float(contribution * 100),
        })

    # Convert to percentage
    coi_pct = float(coi * 100)

    result = {
        "coi_pct": coi_pct,
        "shared_ancestors": ancestor_details,
        "generation_depth": generations,
        "cached": False,
    }

    # Cache result
    if use_cache:
        cache.set(cache_key, result, COI_CACHE_TTL)
        logger.debug(f"COI calculated and cached for {dam_id} x {sire_id}: {coi_pct:.2f}%")

    return result


def calc_coi_by_dogs(
    dam: Dog,
    sire: Dog,
    generations: int = 5,
    use_cache: bool = True
) -> dict:
    """
    Calculate COI using Dog model instances.

    Args:
        dam: Dam Dog instance (must be female)
        sire: Sire Dog instance (must be male)
        generations: Maximum generations to analyze
        use_cache: Whether to use Redis cache

    Returns:
        Same dict as calc_coi()
    """
    if dam.gender != "F":
        raise ValueError(f"Dam must be female, got {dam.gender}")
    if sire.gender != "M":
        raise ValueError(f"Sire must be male, got {sire.gender}")

    return calc_coi(dam.id, sire.id, generations, use_cache)


def get_dam_sire_ancestors(
    dam_id: UUID,
    sire_id: UUID,
    generations: int = 5
) -> tuple:
    """
    Get ancestors of both dam and sire separately.

    Returns:
        Tuple of (dam_ancestors, sire_ancestors) where each is a set of UUIDs
    """
    # Get dam's ancestors
    dam_ancestors = set()
    dam_closures = DogClosure.objects.filter(
        descendant_id=dam_id,
        depth__lte=generations
    ).values_list("ancestor_id", flat=True)
    dam_ancestors.update(dam_closures)
    dam_ancestors.add(dam_id)  # Include self

    # Get sire's ancestors
    sire_ancestors = set()
    sire_closures = DogClosure.objects.filter(
        descendant_id=sire_id,
        depth__lte=generations
    ).values_list("ancestor_id", flat=True)
    sire_ancestors.update(sire_closures)
    sire_ancestors.add(sire_id)  # Include self

    return dam_ancestors, sire_ancestors


def _get_relationship_name(depth_dam: int, depth_sire: int) -> str:
    """
    Get a human-readable relationship name based on depths.

    Args:
        depth_dam: Generations from dam to ancestor
        depth_sire: Generations from sire to ancestor

    Returns:
        Human-readable relationship name
    """
    total = depth_dam + depth_sire

    if depth_dam == 0 or depth_sire == 0:
        return "Direct Parent"
    elif total == 2:
        if depth_dam == 1 and depth_sire == 1:
            return "Full Sibling"
        return "Half Sibling"
    elif total == 3:
        if depth_dam == 1:
            return f"Sire's Parent (Grandparent)"
        return f"Dam's Parent (Grandparent)"
    elif total == 4:
        if depth_dam == 2 and depth_sire == 2:
            return "Full Cousin"
        return "Relative"
    elif total == 5:
        return "Extended Relative"
    else:
        return f"Distant Relative ({total} generations)"


def invalidate_coi_cache(dam_id: UUID, sire_id: UUID, generations: int = 5) -> None:
    """
    Invalidate COI cache for a specific pairing.

    Called when pedigree data changes.
    """
    cache_key = get_cache_key(dam_id, sire_id, generations)
    cache.delete(cache_key)
    logger.debug(f"COI cache invalidated for {dam_id} x {sire_id}")


def get_coi_threshold(coi_pct: float) -> str:
    """
    Get verdict threshold based on COI percentage.

    Returns:
        'SAFE', 'CAUTION', or 'HIGH_RISK'
    """
    if coi_pct < 6.25:
        return "SAFE"
    elif coi_pct < 12.5:
        return "CAUTION"
    else:
        return "HIGH_RISK"


def get_coi_color(coi_pct: float) -> str:
    """
    Get color code for COI percentage (for UI).

    Returns:
        Hex color code
    """
    if coi_pct < 6.25:
        return "#4EAD72"  # Green
    elif coi_pct < 12.5:
        return "#D4920A"  # Yellow/Orange
    else:
        return "#D94040"  # Red
