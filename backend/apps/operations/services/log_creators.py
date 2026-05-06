"""
Service functions for creating ground operation logs.
Used by both routers (with request) and Celery tasks (without request).
"""

from uuid import UUID

from apps.core.models import AuditLog
from ..models import InHeatLog, MatedLog


def create_in_heat_log(dog_id: str, data: dict, idempotency_key: str = None) -> InHeatLog:
    """Create an in-heat log entry from offline queue replay."""
    log = InHeatLog.objects.create(
        dog_id=dog_id,
        draminski_reading=data.get("draminski_reading", 0),
        mating_window=data.get("mating_window", "EARLY"),
        notes=data.get("notes", ""),
    )
    AuditLog.objects.create(
        actor=None,
        action=AuditLog.Action.CREATE,
        resource_type="InHeatLog",
        resource_id=str(log.id),
        payload={"dog_id": dog_id, "idempotency_key": idempotency_key},
    )
    return log


def create_mated_log(dog_id: str, data: dict, idempotency_key: str = None) -> MatedLog:
    """Create a mated log entry from offline queue replay."""
    log = MatedLog.objects.create(
        dog_id=dog_id,
        sire_id=data.get("sire_id"),
        method=data.get("method", "NATURAL"),
        notes=data.get("notes", ""),
    )
    AuditLog.objects.create(
        actor=None,
        action=AuditLog.Action.CREATE,
        resource_type="MatedLog",
        resource_id=str(log.id),
        payload={"dog_id": dog_id, "idempotency_key": idempotency_key},
    )
    return log