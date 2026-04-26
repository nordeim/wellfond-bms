"""
Ground Operations Logs Router
==============================
7 log types for ground staff operations with idempotency.
"""

from typing import List, Optional
from uuid import UUID

from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import get_authenticated_user
from apps.core.permissions import scope_entity
from apps.operations.models import (
    Dog,
    InHeatLog,
    MatedLog,
    WhelpedLog,
    WhelpedPup,
    HealthObsLog,
    WeightLog,
    NursingFlagLog,
    NotReadyLog,
)
from ..schemas import (
    InHeatCreate,
    InHeatResponse,
    MatedCreate,
    MatedResponse,
    WhelpedCreate,
    WhelpedResponse,
    WhelpedPupResponse,
    HealthObsCreate,
    HealthObsResponse,
    WeightCreate,
    WeightResponse,
    NursingFlagCreate,
    NursingFlagResponse,
    NotReadyCreate,
    NotReadyResponse,
    LogsListResponse,
    LogResponse,
)
from ..services.draminski import interpret_for_api
from ..services.alerts import create_alert_event, should_notify

router = Router(tags=["ground-logs"])


def _get_current_user(request):
    """Get current user from session cookie."""
    return get_authenticated_user(request)


def _check_permission(request, dog: Dog):
    """Check if user has access to the dog."""
    user = _get_current_user(request)

    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")

    if user.role != "management" and str(dog.entity_id) != str(user.entity_id):
        raise HttpError(403, "Access denied")

    return user


def _check_idempotency(request, dog_id: str, log_type: str) -> bool:
    """
    Check if this log has already been processed (idempotency).
    Uses X-Idempotency-Key header with Redis.
    """
    from django.core.cache import cache

    idem_key = request.headers.get("X-Idempotency-Key")
    if not idem_key:
        # Missing idempotency key - return error
        raise HttpError(400, "Missing X-Idempotency-Key header")

    cache_key = f"idem:{log_type}:{dog_id}:{idem_key}"
    if cache.get(cache_key):
        # Already processed
        return True

    # Mark as processed (24h TTL)
    cache.set(cache_key, True, timeout=86400)
    return False


# =============================================================================
# In-Heat Logs
# =============================================================================


@router.post("/in-heat/{dog_id}", response=InHeatResponse)
def create_in_heat_log(request, dog_id: UUID, data: InHeatCreate):
    """
    Create an in-heat log with Draminski reading.

    Auto-calculates mating window based on per-dog baseline.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "in_heat"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    # Get Draminski interpretation
    draminski_result = interpret_for_api(str(dog_id), data.draminski_reading)

    # Create log
    log = InHeatLog.objects.create(
        dog=dog,
        draminski_reading=data.draminski_reading,
        mating_window=draminski_result["zone"],
        notes=data.notes or "",
        created_by=user,
    )

    # Create alert event if MATE_NOW
    if draminski_result["zone"] == "MATE_NOW" and should_notify("in_heat", log):
        # This would typically trigger SSE
        pass

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "draminski_reading": log.draminski_reading,
        "mating_window": log.mating_window,
        "notes": log.notes,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# Mated Logs
# =============================================================================


@router.post("/mated/{dog_id}", response=MatedResponse)
def create_mated_log(request, dog_id: UUID, data: MatedCreate):
    """
    Create a mating log with optional dual-sire tracking.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "mated"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    # Resolve sire by chip
    try:
        sire = Dog.objects.get(microchip=data.sire_chip)
    except Dog.DoesNotExist:
        raise HttpError(422, f"Sire with chip {data.sire_chip} not found")

    # Resolve optional sire2
    sire2 = None
    if data.sire2_chip:
        try:
            sire2 = Dog.objects.get(microchip=data.sire2_chip)
        except Dog.DoesNotExist:
            raise HttpError(422, f"Second sire with chip {data.sire2_chip} not found")

    log = MatedLog.objects.create(
        dog=dog,
        sire=sire,
        method=data.method,
        sire2=sire2,
        notes=data.notes or "",
        created_by=user,
    )

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "sire_id": str(log.sire_id),
        "sire_name": log.sire.name,
        "method": log.method,
        "sire2_id": str(log.sire2_id) if log.sire2 else None,
        "sire2_name": log.sire2.name if log.sire2 else None,
        "notes": log.notes,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# Whelped Logs
# =============================================================================


@router.post("/whelped/{dog_id}", response=WhelpedResponse)
def create_whelped_log(request, dog_id: UUID, data: WhelpedCreate):
    """
    Create a whelping log with pup details.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "whelped"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    log = WhelpedLog.objects.create(
        dog=dog,
        method=data.method,
        alive_count=data.alive_count,
        stillborn_count=data.stillborn_count,
        notes=data.notes or "",
        created_by=user,
    )

    # Create pup records
    pups = []
    for pup_data in data.pups:
        pup = WhelpedPup.objects.create(
            log=log,
            gender=pup_data.gender,
            colour=pup_data.colour or "",
            birth_weight=pup_data.birth_weight,
        )
        pups.append({
            "id": str(pup.id),
            "gender": pup.gender,
            "colour": pup.colour,
            "birth_weight": pup.birth_weight,
        })

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "method": log.method,
        "alive_count": log.alive_count,
        "stillborn_count": log.stillborn_count,
        "pups": pups,
        "notes": log.notes,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# Health Observation Logs
# =============================================================================


@router.post("/health-obs/{dog_id}", response=HealthObsResponse)
def create_health_obs_log(request, dog_id: UUID, data: HealthObsCreate):
    """
    Create a health observation log.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "health_obs"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    log = HealthObsLog.objects.create(
        dog=dog,
        category=data.category,
        description=data.description,
        temperature=data.temperature,
        weight=data.weight,
        photos=data.photos or [],
        created_by=user,
    )

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "category": log.category,
        "description": log.description,
        "temperature": log.temperature,
        "weight": log.weight,
        "photos": log.photos,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# Weight Logs
# =============================================================================


@router.post("/weight/{dog_id}", response=WeightResponse)
def create_weight_log(request, dog_id: UUID, data: WeightCreate):
    """
    Create a weight log.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "weight"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    log = WeightLog.objects.create(
        dog=dog,
        weight=data.weight,
        created_by=user,
    )

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "weight": log.weight,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# Nursing Flag Logs
# =============================================================================


@router.post("/nursing-flag/{dog_id}", response=NursingFlagResponse)
def create_nursing_flag_log(request, dog_id: UUID, data: NursingFlagCreate):
    """
    Create a nursing flag log.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "nursing_flag"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    log = NursingFlagLog.objects.create(
        dog=dog,
        section=data.section,
        pup_number=data.pup_number,
        flag_type=data.flag_type,
        photos=data.photos or [],
        severity=data.severity,
        created_by=user,
    )

    # Notify if serious severity
    if should_notify("nursing_flag", log):
        # This would trigger SSE
        pass

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "section": log.section,
        "pup_number": log.pup_number,
        "flag_type": log.flag_type,
        "photos": log.photos,
        "severity": log.severity,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# Not Ready Logs
# =============================================================================


@router.post("/not-ready/{dog_id}", response=NotReadyResponse)
def create_not_ready_log(request, dog_id: UUID, data: NotReadyCreate):
    """
    Create a not-ready log.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check idempotency
    if _check_idempotency(request, str(dog_id), "not_ready"):
        raise HttpError(200, "Already processed")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    log = NotReadyLog.objects.create(
        dog=dog,
        notes=data.notes or "",
        expected_date=data.expected_date,
        created_by=user,
    )

    return {
        "id": str(log.id),
        "dog_id": str(log.dog_id),
        "notes": log.notes,
        "expected_date": log.expected_date,
        "created_at": log.created_at.isoformat(),
        "created_by_name": log.created_by.username if log.created_by else None,
    }


# =============================================================================
# List All Logs
# =============================================================================


@router.get("/{dog_id}", response=LogsListResponse)
def list_logs(request, dog_id: UUID, limit: int = 50):
    """
    List all logs for a dog in chronological order.
    """
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    # Collect all log types
    logs = []

    # In-heat logs
    for log in dog.heat_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "in_heat",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Mating logs
    for log in dog.mating_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "mated",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Whelping logs
    for log in dog.whelping_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "whelped",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Health observation logs
    for log in dog.health_obs_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "health_obs",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Weight logs
    for log in dog.weight_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "weight",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Nursing flag logs
    for log in dog.nursing_flag_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "nursing_flag",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Not ready logs
    for log in dog.not_ready_logs.order_by("-created_at")[:limit]:
        logs.append({
            "id": str(log.id),
            "type": "not_ready",
            "dog_id": str(dog_id),
            "dog_name": dog.name,
            "created_at": log.created_at.isoformat(),
            "created_by_name": log.created_by.username if log.created_by else None,
        })

    # Sort by created_at descending
    logs.sort(key=lambda x: x["created_at"], reverse=True)

    return {"count": len(logs), "results": logs[:limit]}
