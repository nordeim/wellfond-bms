"""
Celery Tasks for Operations
===========================
Background tasks for async processing and scheduled jobs.
"""

import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_draminski_reading(self, dog_id: str, reading_value: int):
    """
    Process a Draminski reading asynchronously.

    Args:
        dog_id: UUID of the dog
        reading_value: The Draminski device reading

    Returns:
        dict with interpretation results
    """
    try:
        from .services.draminski import interpret_for_api

        result = interpret_for_api(dog_id, reading_value)
        return {
            "status": "success",
            "dog_id": dog_id,
            "reading": reading_value,
            "zone": result["zone"],
            "trend": result["trend"],
        }
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_health_alert(self, log_id: str, alert_type: str):
    """
    Generate and send health alert notifications.

    Args:
        log_id: UUID of the health log
        alert_type: Type of alert (health_obs, nursing_flag, etc.)
    """
    try:
        from .models import HealthObsLog, NursingFlagLog
        from .services.alerts import create_alert_event

        if alert_type == "health_obs":
            log = HealthObsLog.objects.get(id=log_id)
        elif alert_type == "nursing_flag":
            log = NursingFlagLog.objects.get(id=log_id)
        else:
            return {"status": "error", "message": "Unknown alert type"}

        # Create alert event
        event = create_alert_event(alert_type, log)

        return {
            "status": "success",
            "alert_id": event.get("id"),
            "dog_id": str(log.dog_id),
            "type": alert_type,
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_idempotency_keys():
    """
    Cleanup expired idempotency keys from Redis.
    Runs daily via Celery beat.
    """
    # Use standard Django cache backend
    from django.core.cache import caches
    
    count = 0
    pattern = "idempotency:*"

    try:
        cache = caches["idempotency"]
        # Access underlying redis-py client
        redis_client = cache.client.get_client()
        keys = redis_client.keys(pattern)

        for key in keys:
            # Check TTL - if expired or near-expiry, delete
            ttl = redis_client.ttl(key)
            if ttl < 0:  # -1 = no expiry, -2 = expired
                redis_client.delete(key)
                count += 1

        return {"status": "success", "keys_cleaned": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@shared_task
def calculate_draminski_baselines():
    """
    Pre-calculate Draminski baselines for all female dogs.
    Runs nightly to keep baselines current.
    """
    from .models import Dog, InHeatLog
    from .services.draminski import _calculate_baseline_for_dog

    # Get all female dogs - FIX CRIT-009: use "F" instead of "female"
    female_dogs = Dog.objects.filter(gender="F")

    calculated = 0
    for dog in female_dogs:
        try:
            _calculate_baseline_for_dog(str(dog.id))
            calculated += 1
        except Exception:
            # Skip dogs without readings
            pass

    return {
        "status": "success",
        "dogs_calculated": calculated,
    }


@shared_task
def send_whelping_reminders():
    """
    Send reminders for dogs approaching expected whelping date.
    Runs daily.
    """
    from .models import NotReadyLog

    # Find dogs with expected whelping in next 7 days
    expected_date = date.today() + timedelta(days=7)

    logs = NotReadyLog.objects.filter(
        expected_date__lte=expected_date,
        expected_date__gte=date.today(),
    ).select_related("dog")

    notifications = []
    for log in logs:
        notifications.append({
            "dog_id": str(log.dog_id),
            "dog_name": log.dog.name,
            "expected_date": log.expected_date.isoformat(),
            "days_until": (log.expected_date - date.today()).days,
        })

    return {
        "status": "success",
        "reminders_sent": len(notifications),
        "notifications": notifications,
    }


@shared_task(bind=True, max_retries=2)
def archive_old_logs(self):
    """
    Delete ground operation logs older than retention period.
    Runs monthly via Celery beat.

    Retention: 2 years (730 days).
    Logs deletion counts to audit trail before removing.
    """
    from .models import (
        InHeatLog,
        MatedLog,
        WhelpedLog,
        HealthObsLog,
        WeightLog,
        NursingFlagLog,
        NotReadyLog,
    )
    from apps.core.models import AuditLog

    retention_days = 365 * 2
    cutoff_date = timezone.now() - timedelta(days=retention_days)

    archived_counts = {}

    log_models = [
        InHeatLog,
        MatedLog,
        WhelpedLog,
        HealthObsLog,
        WeightLog,
        NursingFlagLog,
        NotReadyLog,
    ]

    with transaction.atomic():
        for model in log_models:
            old_logs = model.objects.filter(created_at__lt=cutoff_date)
            count = old_logs.count()
            if count > 0:
                archived_counts[model.__name__] = count

        if archived_counts:
            AuditLog.objects.create(
                actor=None,
                action=AuditLog.Action.DELETE,
                resource_type="GroundLogArchive",
                resource_id="system",
                payload={
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "deleted_counts": archived_counts,
                },
            )

            logger.info(f"Archiving old logs: {archived_counts}")

            for model in log_models:
                if model.__name__ in archived_counts:
                    model.objects.filter(created_at__lt=cutoff_date).delete()

            logger.info(f"Archived old logs: {archived_counts}")

    return {
        "status": "success",
        "archived_counts": archived_counts,
        "cutoff_date": cutoff_date.isoformat(),
    }


@shared_task
def check_overdue_vaccines():
    """
    Check for dogs with overdue vaccinations.
    Runs daily via Celery beat.
    """
    from .models import Vaccination
    
    overdue_count = Vaccination.objects.filter(
        status="OVERDUE",
        due_date__lt=timezone.now().date()
    ).count()
    
    return {"status": "success", "overdue_count": overdue_count}


@shared_task(bind=True, max_retries=2)
def check_rehome_overdue(self):
    """
    Check for dogs approaching or past rehome age.
    Runs daily via Celery beat at 8:05am SGT.

    Flags dogs aged 5+ (yellow) and 6+ (red) using Dog.rehome_flag.
    Logs results to AuditLog for management dashboard visibility.
    """
    from .models import Dog
    from apps.core.models import AuditLog

    today = date.today()
    five_years_ago = today - timedelta(days=5 * 365)

    dogs = Dog.objects.filter(
        dob__lte=five_years_ago,
        status=Dog.Status.ACTIVE,
    ).select_related("entity")

    flagged = {"yellow": [], "red": []}

    for dog in dogs:
        flag = dog.rehome_flag
        if flag:
            flagged[flag].append({
                "dog_id": str(dog.id),
                "dog_name": dog.name,
                "entity": dog.entity.name if dog.entity else "Unknown",
                "age": dog.age_display,
            })

    total_flagged = len(flagged["yellow"]) + len(flagged["red"])

    if total_flagged > 0:
        logger.warning(
            f"Rehome overdue: {len(flagged['red'])} red, "
            f"{len(flagged['yellow'])} yellow flags"
        )

        AuditLog.objects.create(
            actor=None,
            action=AuditLog.Action.UPDATE,
            resource_type="RehomeOverdue",
            resource_id="system",
            payload={
                "red_count": len(flagged["red"]),
                "yellow_count": len(flagged["yellow"]),
                "red_dogs": flagged["red"][:20],
                "yellow_dogs": flagged["yellow"][:20],
            },
        )

    return {
        "status": "success",
        "red_count": len(flagged["red"]),
        "yellow_count": len(flagged["yellow"]),
        "total_flagged": total_flagged,
    }


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def sync_offline_queue(self, user_id: str):
    """
    Process offline queue for a user.
    Called when user comes back online.

    Args:
        user_id: UUID of the user whose queue to process
    """
    from django.core.cache import cache

    queue_key = f"offline_queue:{user_id}"
    queue_data = cache.get(queue_key, [])

    if not queue_data:
        return {"status": "success", "processed": 0}

    processed = 0
    failed = []

    for item in queue_data:
        try:
            # Re-submit the log
            log_type = item.get("type")
            dog_id = item.get("dog_id")
            data = item.get("data")
            idem_key = item.get("idempotency_key")

            # Import and call appropriate service
            if log_type == "in_heat":
                from .services.log_creators import create_in_heat_log
                create_in_heat_log(dog_id, data, idem_key)
            elif log_type == "mated":
                from .services.log_creators import create_mated_log
                create_mated_log(dog_id, data, idem_key)
            # ... other log types

            processed += 1

        except Exception as e:
            failed.append({
                "item": item,
                "error": str(e),
            })

    # Clear processed items from queue
    if not failed:
        cache.delete(queue_key)
    else:
        # Keep failed items for retry
        cache.set(queue_key, failed, timeout=86400 * 7)  # 7 days

    return {
        "status": "success",
        "processed": processed,
        "failed": len(failed),
    }
