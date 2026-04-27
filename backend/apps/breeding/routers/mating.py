"""
Mating Router
=============
Phase 4: Breeding & Genetics Engine

Endpoints:
- POST /api/v1/breeding/mate-check - Calculate COI and saturation
- POST /api/v1/breeding/mate-check/override - Create override audit
- GET /api/v1/breeding/mate-check/history - List override history
"""

import logging
from typing import List

from typing import List

from django.db import IntegrityError
from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import AuthenticationService
from apps.core.models import AuditLog
from apps.core.permissions import require_entity_access, require_role
from apps.operations.models import Dog

from ..models import MateCheckOverride
from ..schemas import (
    MateCheckRequest,
    MateCheckResponse,
    OverrideCreate,
    OverrideListItem,
    OverrideResponse,
)
from ..services.coi import calc_coi, get_coi_threshold
from ..services.saturation import calc_saturation

logger = logging.getLogger(__name__)

router = Router(tags=["breeding"])


@router.post("/mate-check", response=MateCheckResponse)
def mate_check(request, data: MateCheckRequest):
    """
    Calculate COI and farm saturation for a proposed mating.

    Accepts dam and sire microchips, returns COI percentage,
    saturation percentage, and verdict (SAFE/CAUTION/HIGH_RISK).
    """
    # Validate user has entity access
    require_entity_access(request)

    # Find dogs by microchip
    dam = Dog.objects.filter(
        microchip=data.dam_chip,
        gender="F"
    ).select_related("entity").first()

    if not dam:
        raise HttpError(404, f"Dam not found with microchip: {data.dam_chip}")

    sire1 = Dog.objects.filter(
        microchip=data.sire1_chip,
        gender="M"
    ).select_related("entity").first()

    if not sire1:
        raise HttpError(404, f"Sire not found with microchip: {data.sire1_chip}")

    # Validate entity scoping - dam and sire must be in same entity
    if dam.entity_id != sire1.entity_id:
        raise HttpError(400, "Dam and sire must belong to the same entity")

    # Check user has access to this entity
    user = AuthenticationService.get_user_from_request(request)
    if user and not user.has_role("management"):
        if user.entity_id != dam.entity_id:
            raise HttpError(403, "You do not have access to dogs in this entity")

    # Optional second sire (dual-sire breeding)
    sire2 = None
    if data.sire2_chip:
        sire2 = Dog.objects.filter(
            microchip=data.sire2_chip,
            gender="M"
        ).select_related("entity").first()

        if not sire2:
            raise HttpError(404, f"Sire 2 not found with microchip: {data.sire2_chip}")

        if sire2.entity_id != dam.entity_id:
            raise HttpError(400, "All dogs must belong to the same entity")

    # Calculate COI
    try:
        coi_result = calc_coi(dam.id, sire1.id, generations=5)
    except Exception as e:
        logger.error(f"COI calculation failed: {e}")
        raise HttpError(500, "Failed to calculate COI")

    # Calculate saturation
    try:
        saturation_result = calc_saturation(sire1.id, dam.entity_id)
    except Exception as e:
        logger.error(f"Saturation calculation failed: {e}")
        raise HttpError(500, "Failed to calculate farm saturation")

    # Determine verdict based on COI and saturation
    coi_verdict = get_coi_threshold(coi_result["coi_pct"])
    saturation_verdict = saturation_result.get_threshold()

    # Overall verdict is the worse of the two
    verdict_priority = {"SAFE": 0, "CAUTION": 1, "HIGH_RISK": 2}
    overall_verdict = coi_verdict
    if verdict_priority[saturation_verdict] > verdict_priority[coi_verdict]:
        overall_verdict = saturation_verdict

    # Build response
    response_data = {
        "coi_pct": coi_result["coi_pct"],
        "saturation_pct": saturation_result.saturation_pct,
        "verdict": overall_verdict,
        "shared_ancestors": coi_result["shared_ancestors"],
    }

    logger.info(
        f"Mate check performed: {dam.name} x {sire1.name} "
        f"(COI: {coi_result['coi_pct']:.2f}%, "
        f"Saturation: {saturation_result.saturation_pct:.2f}%, "
        f"Verdict: {overall_verdict})"
    )

    return response_data


@router.post("/mate-check/override", response=OverrideResponse)
def create_override(request, data: OverrideCreate):
    """
    Create a mate check override with audit trail.

    Requires reason and optional notes. Logs to AuditLog.
    Only admin/sales/management roles can create overrides.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Only specific roles can override
    if not user.has_role("admin", "sales", "management"):
        raise HttpError(403, "Only admin, sales, or management can create overrides")

    # Get the COI data from request (frontend must provide)
    # This is passed in the request body alongside the reason
    coi_pct = getattr(request, "coi_pct", 0)
    saturation_pct = getattr(request, "saturation_pct", 0)
    verdict = getattr(request, "verdict", "SAFE")
    dam_id = getattr(request, "dam_id", None)
    sire1_id = getattr(request, "sire1_id", None)
    sire2_id = getattr(request, "sire2_id", None)

    if not dam_id or not sire1_id:
        raise HttpError(400, "Missing dog IDs for override")

    # Validate dogs exist
    dam = Dog.objects.filter(id=dam_id).first()
    sire1 = Dog.objects.filter(id=sire1_id).first()

    if not dam or not sire1:
        raise HttpError(404, "Dogs not found")

    # Create override record
    try:
        override = MateCheckOverride.objects.create(
            dam=dam,
            sire1=sire1,
            sire2=Dog.objects.filter(id=sire2_id).first() if sire2_id else None,
            coi_pct=coi_pct,
            saturation_pct=saturation_pct,
            verdict=verdict,
            override_reason=data.reason,
            override_notes=data.notes or "",
            staff=user,
            entity=dam.entity,
        )
    except IntegrityError as e:
        logger.error(f"Failed to create override: {e}")
        raise HttpError(500, "Failed to create override record")

    # Log to audit trail
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.CREATE,
        resource_type="MateCheckOverride",
        resource_id=str(override.id),
        payload={
            "dam_id": str(dam.id),
            "sire1_id": str(sire1.id),
            "coi_pct": coi_pct,
            "saturation_pct": saturation_pct,
            "verdict": verdict,
            "reason": data.reason,
        },
    )

    logger.info(
        f"Mate check override created by {user.email}: "
        f"{dam.name} x {sire1.name} - Reason: {data.reason}"
    )

    # Build response
    return {
        "id": override.id,
        "dam_id": dam.id,
        "dam_name": dam.name,
        "sire1_id": sire1.id,
        "sire1_name": sire1.name,
        "sire2_id": override.sire2.id if override.sire2 else None,
        "sire2_name": override.sire2.name if override.sire2 else None,
        "coi_pct": override.coi_pct,
        "saturation_pct": override.saturation_pct,
        "verdict": override.verdict,
        "override_reason": override.override_reason,
        "override_notes": override.override_notes,
        "staff_name": user.get_full_name() or user.email,
        "staff_role": user.role,
        "created_at": override.created_at.isoformat(),
    }


@router.get("/mate-check/history", response=List[OverrideListItem])
def list_overrides(request, page: int = 1, per_page: int = 20):
    """
    List mate check override history.

    Returns paginated list of overrides with dam/sire details.
    Scoped to user's entity unless management role.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Build queryset
    queryset = MateCheckOverride.objects.select_related(
        "dam", "sire1", "sire2", "staff", "entity"
    ).order_by("-created_at")

    # Apply entity scoping
    if not user.has_role("management"):
        queryset = queryset.filter(entity_id=user.entity_id)

    # Manual pagination
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    page_qs = queryset[start:end]

    # Convert to response format
    overrides = []
    for override in page_qs:
        overrides.append({
            "id": override.id,
            "dam_id": override.dam.id,
            "dam_name": override.dam.name,
            "sire1_id": override.sire1.id,
            "sire1_name": override.sire1.name,
            "sire2_id": override.sire2.id if override.sire2 else None,
            "sire2_name": override.sire2.name if override.sire2 else None,
            "coi_pct": override.coi_pct,
            "saturation_pct": override.saturation_pct,
            "verdict": override.verdict,
            "override_reason": override.override_reason,
            "override_notes": override.override_notes,
            "staff_name": override.staff.get_full_name() or override.staff.email,
            "staff_role": override.staff.role,
            "created_at": override.created_at.isoformat(),
        })

    return overrides
