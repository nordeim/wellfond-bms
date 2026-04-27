"""
Litters Router
==============
Phase 4: Breeding & Genetics Engine

Endpoints:
- GET /api/v1/breeding/litters/ - List litters with filters
- POST /api/v1/breeding/litters/ - Create litter
- GET /api/v1/breeding/litters/{id} - Get litter detail with puppies
- PATCH /api/v1/breeding/litters/{id} - Update litter
- POST /api/v1/breeding/litters/{id}/puppies - Add puppy to litter
- PATCH /api/v1/breeding/litters/{id}/puppies/{puppy_id} - Update puppy
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import AuthenticationService
from apps.core.models import AuditLog
from apps.core.permissions import require_entity_access, require_role
from apps.operations.models import Dog

from ..models import BreedingRecord, Litter, Puppy
from ..schemas import (
    LitterCreate,
    LitterDetail,
    LitterFilters,
    LitterListItem,
    LitterUpdate,
    PaginatedLitters,
    PuppyCreate,
    PuppyDetail,
    PuppyListItem,
    PuppyUpdate,
)
from ..tasks import trigger_closure_rebuild

logger = logging.getLogger(__name__)

router = Router(tags=["litters"])


@router.get("/litters", response=List[LitterListItem])
def list_litters(request, dam_chip: str = None, sire_chip: str = None, whelp_date_from: date = None, whelp_date_to: date = None, page: int = 1, per_page: int = 20):
    """
    List litters with optional filters.

    Returns paginated litters scoped to user's entity.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Build queryset
    queryset = Litter.objects.select_related(
        "breeding_record",
        "breeding_record__dam",
        "breeding_record__sire1",
        "breeding_record__sire2",
    ).prefetch_related("puppies").order_by("-whelp_date")

    # Apply entity scoping
    if not user.has_role("management"):
        queryset = queryset.filter(entity_id=user.entity_id)

    # Apply filters
    if dam_chip:
        queryset = queryset.filter(
            breeding_record__dam__microchip__icontains=dam_chip
        )
    if sire_chip:
        queryset = queryset.filter(
            breeding_record__sire1__microchip__icontains=sire_chip
        ) | queryset.filter(
            breeding_record__sire2__microchip__icontains=sire_chip
        )
    if whelp_date_from:
        queryset = queryset.filter(whelp_date__gte=whelp_date_from)
    if whelp_date_to:
        queryset = queryset.filter(whelp_date__lte=whelp_date_to)

    # Manual pagination
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    page_qs = queryset[start:end]

    # Build response
    litters = []
    for litter in page_qs:
        litters.append({
            "id": litter.id,
            "breeding_record_id": litter.breeding_record_id,
            "dam_name": litter.breeding_record.dam.name,
            "sire_name": litter.breeding_record.sire1.name,
            "whelp_date": litter.whelp_date,
            "alive_count": litter.alive_count,
            "stillborn_count": litter.stillborn_count,
            "total_count": litter.total_count,
            "delivery_method": litter.delivery_method,
            "puppy_count": litter.puppies.count(),
        })

    return litters


@router.post("/litters", response=LitterDetail)
def create_litter(request, data: LitterCreate):
    """
    Create a new litter record.

    Links to an existing breeding record. Triggers closure table rebuild.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check breeding record exists
    breeding_record = BreedingRecord.objects.filter(
        id=data.breeding_record_id
    ).select_related("dam", "sire1", "sire2").first()

    if not breeding_record:
        raise HttpError(404, "Breeding record not found")

    # Check entity access
    if not user.has_role("management") and user.entity_id != breeding_record.entity_id:
        raise HttpError(403, "You do not have access to this breeding record")

    # Check litter doesn't already exist
    if hasattr(breeding_record, "litter"):
        raise HttpError(400, "Litter already exists for this breeding record")

    # Create litter
    try:
        litter = Litter.objects.create(
            breeding_record=breeding_record,
            whelp_date=data.whelp_date,
            delivery_method=data.delivery_method,
            alive_count=data.alive_count,
            stillborn_count=data.stillborn_count,
            notes=data.notes or "",
            entity=breeding_record.entity,
            created_by=user,
        )
    except Exception as e:
        logger.error(f"Failed to create litter: {e}")
        raise HttpError(500, "Failed to create litter")

    # Trigger async closure table rebuild
    trigger_closure_rebuild.delay(full_rebuild=False, dog_id=str(breeding_record.dam.id))
    if breeding_record.sire1:
        trigger_closure_rebuild.delay(full_rebuild=False, dog_id=str(breeding_record.sire1.id))
    if breeding_record.sire2:
        trigger_closure_rebuild.delay(full_rebuild=False, dog_id=str(breeding_record.sire2.id))

    # Log to audit
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.CREATE,
        resource_type="Litter",
        resource_id=str(litter.id),
        payload={
            "breeding_record_id": str(breeding_record.id),
            "whelp_date": str(data.whelp_date),
            "alive_count": data.alive_count,
            "stillborn_count": data.stillborn_count,
        },
    )

    logger.info(f"Litter created: {litter} by {user.email}")

    # Return full detail
    return get_litter_detail(litter)


@router.get("/litters/{litter_id}", response=LitterDetail)
def get_litter(request, litter_id: UUID):
    """
    Get litter detail with puppies.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    litter = Litter.objects.select_related(
        "breeding_record",
        "breeding_record__dam",
        "breeding_record__sire1",
        "breeding_record__sire2",
    ).prefetch_related("puppies").filter(id=litter_id).first()

    if not litter:
        raise HttpError(404, "Litter not found")

    # Check entity access
    if not user.has_role("management") and user.entity_id != litter.entity_id:
        raise HttpError(403, "You do not have access to this litter")

    return get_litter_detail(litter)


@router.patch("/litters/{litter_id}", response=LitterDetail)
def update_litter(request, litter_id: UUID, data: LitterUpdate):
    """
    Update litter details.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    litter = Litter.objects.filter(id=litter_id).first()
    if not litter:
        raise HttpError(404, "Litter not found")

    # Check entity access
    if not user.has_role("management") and user.entity_id != litter.entity_id:
        raise HttpError(403, "You do not have access to this litter")

    # Update fields
    if data.whelp_date:
        litter.whelp_date = data.whelp_date
    if data.delivery_method:
        litter.delivery_method = data.delivery_method
    if data.alive_count is not None:
        litter.alive_count = data.alive_count
    if data.stillborn_count is not None:
        litter.stillborn_count = data.stillborn_count
    if data.notes is not None:
        litter.notes = data.notes

    litter.save()

    # Log to audit
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.UPDATE,
        resource_type="Litter",
        resource_id=str(litter.id),
        payload={
            "alive_count": litter.alive_count,
            "stillborn_count": litter.stillborn_count,
        },
    )

    logger.info(f"Litter updated: {litter.id} by {user.email}")

    # Refresh and return
    litter = Litter.objects.select_related(
        "breeding_record",
        "breeding_record__dam",
        "breeding_record__sire1",
        "breeding_record__sire2",
    ).prefetch_related("puppies").get(id=litter_id)

    return get_litter_detail(litter)


@router.post("/litters/{litter_id}/puppies", response=PuppyDetail)
def add_puppy(request, litter_id: UUID, data: PuppyCreate):
    """
    Add a puppy to a litter.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    litter = Litter.objects.select_related("breeding_record").filter(id=litter_id).first()
    if not litter:
        raise HttpError(404, "Litter not found")

    # Check entity access
    if not user.has_role("management") and user.entity_id != litter.entity_id:
        raise HttpError(403, "You do not have access to this litter")

    # Check microchip uniqueness if provided
    if data.microchip:
        existing = Puppy.objects.filter(microchip=data.microchip).first()
        if existing:
            raise HttpError(400, f"Microchip {data.microchip} already exists")

    # Create puppy
    try:
        puppy = Puppy.objects.create(
            litter=litter,
            microchip=data.microchip,
            gender=data.gender,
            colour=data.colour,
            birth_weight=data.birth_weight,
            confirmed_sire=data.confirmed_sire or "UNCONFIRMED",
            paternity_method=data.paternity_method or "UNCONFIRMED",
            entity=litter.entity,
        )
    except Exception as e:
        logger.error(f"Failed to create puppy: {e}")
        raise HttpError(500, "Failed to create puppy")

    # Update litter alive count
    litter.alive_count += 1
    litter.save(update_fields=["alive_count", "total_count"])

    # Log to audit
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.CREATE,
        resource_type="Puppy",
        resource_id=str(puppy.id),
        payload={
            "litter_id": str(litter.id),
            "gender": data.gender,
            "colour": data.colour,
        },
    )

    logger.info(f"Puppy added to litter {litter_id}: {puppy.gender} by {user.email}")

    return {
        "id": puppy.id,
        "litter_id": litter.id,
        "dam_name": litter.breeding_record.dam.name,
        "sire_name": litter.breeding_record.sire1.name,
        "whelp_date": litter.whelp_date,
        "microchip": puppy.microchip,
        "gender": puppy.gender,
        "colour": puppy.colour,
        "birth_weight": puppy.birth_weight,
        "confirmed_sire": puppy.confirmed_sire,
        "paternity_method": puppy.paternity_method,
        "status": puppy.status,
        "buyer_name": puppy.buyer_name,
        "buyer_contact": puppy.buyer_contact,
        "sale_date": puppy.sale_date,
        "created_at": puppy.created_at.isoformat(),
        "updated_at": puppy.updated_at.isoformat(),
    }


@router.patch("/litters/{litter_id}/puppies/{puppy_id}", response=PuppyDetail)
def update_puppy(
    request,
    litter_id: UUID,
    puppy_id: UUID,
    data: PuppyUpdate
):
    """
    Update a puppy's details.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    puppy = Puppy.objects.select_related("litter__breeding_record").filter(
        id=puppy_id,
        litter_id=litter_id
    ).first()

    if not puppy:
        raise HttpError(404, "Puppy not found")

    # Check entity access
    if not user.has_role("management") and user.entity_id != puppy.entity_id:
        raise HttpError(403, "You do not have access to this puppy")

    # Check microchip uniqueness if changing
    if data.microchip and data.microchip != puppy.microchip:
        existing = Puppy.objects.filter(microchip=data.microchip).exclude(id=puppy_id).first()
        if existing:
            raise HttpError(400, f"Microchip {data.microchip} already exists")

    # Update fields
    if data.microchip is not None:
        puppy.microchip = data.microchip
    if data.colour is not None:
        puppy.colour = data.colour
    if data.birth_weight is not None:
        puppy.birth_weight = data.birth_weight
    if data.confirmed_sire is not None:
        puppy.confirmed_sire = data.confirmed_sire
    if data.paternity_method is not None:
        puppy.paternity_method = data.paternity_method
    if data.status is not None:
        puppy.status = data.status
    if data.buyer_name is not None:
        puppy.buyer_name = data.buyer_name
    if data.buyer_contact is not None:
        puppy.buyer_contact = data.buyer_contact
    if data.sale_date is not None:
        puppy.sale_date = data.sale_date

    puppy.save()

    # Log to audit
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.UPDATE,
        resource_type="Puppy",
        resource_id=str(puppy.id),
        payload={
            "microchip": puppy.microchip,
            "status": puppy.status,
        },
    )

    logger.info(f"Puppy updated: {puppy.id} by {user.email}")

    return {
        "id": puppy.id,
        "litter_id": puppy.litter.id,
        "dam_name": puppy.litter.breeding_record.dam.name,
        "sire_name": puppy.litter.breeding_record.sire1.name,
        "whelp_date": puppy.litter.whelp_date,
        "microchip": puppy.microchip,
        "gender": puppy.gender,
        "colour": puppy.colour,
        "birth_weight": puppy.birth_weight,
        "confirmed_sire": puppy.confirmed_sire,
        "paternity_method": puppy.paternity_method,
        "status": puppy.status,
        "buyer_name": puppy.buyer_name,
        "buyer_contact": puppy.buyer_contact,
        "sale_date": puppy.sale_date,
        "created_at": puppy.created_at.isoformat(),
        "updated_at": puppy.updated_at.isoformat(),
    }


def get_litter_detail(litter: Litter) -> dict:
    """Helper to build litter detail response."""
    puppies = []
    for puppy in litter.puppies.all():
        puppies.append({
            "id": puppy.id,
            "litter_id": litter.id,
            "microchip": puppy.microchip,
            "gender": puppy.gender,
            "colour": puppy.colour,
            "birth_weight": puppy.birth_weight,
            "confirmed_sire": puppy.confirmed_sire,
            "paternity_method": puppy.paternity_method,
            "status": puppy.status,
            "buyer_name": puppy.buyer_name,
            "sale_date": puppy.sale_date,
        })

    return {
        "id": litter.id,
        "breeding_record_id": litter.breeding_record_id,
        "dam_id": litter.breeding_record.dam.id,
        "dam_name": litter.breeding_record.dam.name,
        "dam_microchip": litter.breeding_record.dam.microchip,
        "sire1_id": litter.breeding_record.sire1.id,
        "sire1_name": litter.breeding_record.sire1.name,
        "sire1_microchip": litter.breeding_record.sire1.microchip,
        "sire2_id": litter.breeding_record.sire2.id if litter.breeding_record.sire2 else None,
        "sire2_name": litter.breeding_record.sire2.name if litter.breeding_record.sire2 else None,
        "sire2_microchip": litter.breeding_record.sire2.microchip if litter.breeding_record.sire2 else None,
        "whelp_date": litter.whelp_date,
        "delivery_method": litter.delivery_method,
        "alive_count": litter.alive_count,
        "stillborn_count": litter.stillborn_count,
        "total_count": litter.total_count,
        "notes": litter.notes,
        "puppies": puppies,
        "created_by_name": litter.created_by.get_full_name() if litter.created_by else None,
        "created_at": litter.created_at.isoformat(),
        "updated_at": litter.updated_at.isoformat(),
    }
