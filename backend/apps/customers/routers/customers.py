"""Customers Router
==================
Phase 7: Customer DB & Marketing Blast

Customer CRUD, segmentation, blast dispatch, and communication logs.
"""

import base64
import csv
import io
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from django.db.models import Q, QuerySet
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate

from apps.core.auth import get_authenticated_user
from apps.core.permissions import require_role, scope_entity

from ..models import Customer, CommunicationLog, Segment
from ..schemas import (
    BlastCreate,
    BlastPreviewResponse,
    BlastProgress,
    BlastResult,
    CSVImportPreview,
    CSVImportRequest,
    CSVImportResponse,
    CustomerCreate,
    CustomerDetailOut,
    CustomerFilters,
    CustomerListResponse,
    CustomerUpdate,
    PDPAConsentUpdate,
    SegmentCreate,
    SegmentOut,
    SegmentPreviewResponse,
    SegmentUpdate,
)
from ..services.segmentation import SegmentationService
from ..services.blast import BlastService

logger = logging.getLogger(__name__)

router = Router(tags=["customers"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_customer_queryset(request) -> QuerySet:
    """Get scoped customer queryset for current user."""
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")
    queryset = scope_entity(Customer.objects.all(), user)
    return queryset.select_related("entity")


# =============================================================================
# Customer List & Detail Endpoints
# =============================================================================

@router.get("/", response=CustomerListResponse)
def list_customers(
    request,
    search: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    pdpa_consent: Optional[bool] = None,
    housing_type: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
):
    """
    List customers with filters and pagination.
    """
    queryset = get_customer_queryset(request)

    # Apply filters
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(mobile__icontains=search)
            | Q(email__icontains=search)
        )

    if entity_id:
        queryset = queryset.filter(entity_id=entity_id)

    if pdpa_consent is not None:
        queryset = queryset.filter(pdpa_consent=pdpa_consent)

    if housing_type:
        queryset = queryset.filter(housing_type=housing_type)

    # Count before pagination
    total = queryset.count()

    # Apply pagination
    offset = (page - 1) * per_page
    customers = queryset[offset : offset + per_page]

    items = [
        {
            "id": c.id,
            "name": c.name,
            "mobile": c.mobile,
            "email": c.email,
            "housing_type": c.housing_type,
            "pdpa_consent": c.pdpa_consent,
            "entity_id": c.entity_id,
            "entity_name": c.entity.name,
            "created_at": c.created_at,
        }
        for c in customers
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{customer_id}", response=dict)
def get_customer(request, customer_id: UUID):
    """
    Get customer details with communication history.
    """
    queryset = get_customer_queryset(request)

    try:
        customer = queryset.get(id=customer_id)
    except Customer.DoesNotExist:
        raise HttpError(404, "Customer not found")

    # Get communication logs
    logs = CommunicationLog.objects.filter(customer=customer).order_by("-created_at")[:50]

    return {
        "id": customer.id,
        "name": customer.name,
        "nric": customer.nric,
        "mobile": customer.mobile,
        "email": customer.email,
        "address": customer.address,
        "housing_type": customer.housing_type,
        "pdpa_consent": customer.pdpa_consent,
        "pdpa_consent_date": customer.pdpa_consent_date,
        "entity_id": customer.entity_id,
        "entity_name": customer.entity.name,
        "notes": customer.notes,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        "comms_log": [
            {
                "id": log.id,
                "channel": log.channel,
                "status": log.status,
                "subject": log.subject,
                "message_preview": log.message_preview,
                "created_at": log.created_at,
                "sent_at": log.sent_at,
            }
            for log in logs
        ],
    }


@router.post("/", response=dict)
def create_customer(request, payload: CustomerCreate):
    """
    Create a new customer.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Check for duplicate mobile
    if Customer.objects.filter(mobile=payload.mobile).exists():
        raise HttpError(409, "Customer with this mobile number already exists")

    customer = Customer.objects.create(
        name=payload.name,
        nric=payload.nric or "",
        mobile=payload.mobile,
        email=payload.email or "",
        address=payload.address or "",
        housing_type=payload.housing_type or "",
        pdpa_consent=payload.pdpa_consent,
        pdpa_consent_date=datetime.now() if payload.pdpa_consent else None,
        entity_id=payload.entity_id,
        created_by=user,
        notes=payload.notes or "",
    )

    return {"id": customer.id, "message": "Customer created successfully"}


@router.patch("/{customer_id}", response=dict)
def update_customer(request, customer_id: UUID, payload: CustomerUpdate):
    """
    Update customer details.
    """
    queryset = get_customer_queryset(request)

    try:
        customer = queryset.get(id=customer_id)
    except Customer.DoesNotExist:
        raise HttpError(404, "Customer not found")

    # Update fields
    update_data = payload.model_dump(exclude_unset=True)

    # Handle PDPA consent change
    if "pdpa_consent" in update_data:
        if update_data["pdpa_consent"] and not customer.pdpa_consent:
            # Opting in
            customer.pdpa_consent_date = datetime.now()
        elif not update_data["pdpa_consent"] and customer.pdpa_consent:
            # Opting out
            customer.pdpa_consent_date = None

    for field, value in update_data.items():
        if field != "entity_id":  # Don't allow entity change
            setattr(customer, field, value)

    customer.save()

    return {"id": customer.id, "message": "Customer updated successfully"}


# =============================================================================
# Segment Endpoints
# =============================================================================

@router.get("/segments/", response=list[SegmentOut])
def list_segments(request):
    """
    List all segments.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    queryset = scope_entity(Segment.objects.all(), user)
    segments = queryset.order_by("-created_at")

    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "filters_json": s.filters_json,
            "customer_count": s.customer_count,
            "count_updated_at": s.count_updated_at,
            "entity_id": s.entity_id,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in segments
    ]


@router.post("/segments/", response=dict)
def create_segment(request, payload: SegmentCreate):
    """
    Create a new segment.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    segment = Segment.objects.create(
        name=payload.name,
        description=payload.description or "",
        filters_json=payload.filters.model_dump(),
        entity_id=payload.entity_id,
        created_by=user,
    )

    # Calculate initial count
    count = SegmentationService.preview_segment(segment.filters_json)
    segment.customer_count = count
    segment.count_updated_at = datetime.now()
    segment.save()

    return {"id": segment.id, "count": count, "message": "Segment created"}


@router.get("/segments/{segment_id}/preview", response=SegmentPreviewResponse)
def preview_segment(request, segment_id: UUID):
    """
    Preview segment count without creating blast.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        segment = scope_entity(Segment.objects.all(), user).get(id=segment_id)
    except Segment.DoesNotExist:
        raise HttpError(404, "Segment not found")

    count = SegmentationService.preview_segment(segment.filters_json)

    return {
        "count": count,
        "filters_applied": segment.filters_json,
    }


# =============================================================================
# Blast Endpoints
# =============================================================================

@router.post("/blast/preview", response=BlastPreviewResponse)
def preview_blast(request, payload: BlastCreate):
    """
    Preview blast recipients before sending.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Get recipient list
    recipients = BlastService.get_recipients(payload)
    total = len(recipients)

    # Apply PDPA filter
    eligible = [r for r in recipients if r.pdpa_consent]
    excluded = total - len(eligible)

    # Generate sample message
    sample = None
    if eligible:
        sample = BlastService.apply_merge_tags(
            payload.body,
            eligible[0],
            payload.merge_tags or {},
        )[:200]

    return {
        "total_customers": total,
        "eligible_customers": len(eligible),
        "excluded_customers": excluded,
        "excluded_reason": "PDPA consent opt-out",
        "channel": payload.channel.value if hasattr(payload.channel, "value") else str(payload.channel),
        "sample_message": sample,
    }


@router.post("/blast", response=BlastResult)
def send_blast(request, payload: BlastCreate):
    """
    Send marketing blast to segment or customer list.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    blast_id = uuid4()
    result = BlastService.send_blast(blast_id, payload, user)

    return result


@router.get("/blast/{blast_id}/progress")
def get_blast_progress(request, blast_id: UUID):
    """
    Get blast progress for SSE streaming.
    """
    from ..services.blast import BlastProgressTracker

    tracker = BlastProgressTracker(blast_id)
    progress = tracker.get_progress()

    return progress


# =============================================================================
# PDPA Consent Endpoints
# =============================================================================

@router.patch("/{customer_id}/consent", response=dict)
def update_consent(request, customer_id: UUID, payload: PDPAConsentUpdate):
    """
    Update customer PDPA consent status.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    queryset = scope_entity(Customer.objects.all(), user)

    try:
        customer = queryset.get(id=customer_id)
    except Customer.DoesNotExist:
        raise HttpError(404, "Customer not found")

    old_consent = customer.pdpa_consent
    customer.pdpa_consent = payload.consent

    if payload.consent and not old_consent:
        customer.pdpa_consent_date = datetime.now()
    elif not payload.consent and old_consent:
        customer.pdpa_consent_date = None

    customer.save()

    # Log consent change (for Phase 7, simple version)
    logger.info(
        f"PDPA consent change: customer={customer_id}, "
        f"from={old_consent}, to={payload.consent}, actor={user.id}"
    )

    return {
        "customer_id": customer_id,
        "is_consented": payload.consent,
        "last_updated": datetime.now(),
    }


# =============================================================================
# CSV Import Endpoints
# =============================================================================

@router.post("/import/preview", response=CSVImportPreview)
def preview_csv_import(request, payload: CSVImportRequest):
    """
    Preview CSV import before committing.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        csv_content = base64.b64decode(payload.file_content).decode("utf-8")
    except Exception as e:
        raise HttpError(400, f"Invalid file content: {e}")

    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    total = len(rows)
    valid = 0
    duplicates = 0
    invalid = 0
    sample = []

    for i, row in enumerate(rows):
        # Check required fields
        mapping = payload.column_mapping
        name = row.get(mapping.name_column, "").strip()
        mobile = row.get(mapping.mobile_column, "").strip()

        if not name or not mobile:
            invalid += 1
            continue

        # Check for duplicates
        if payload.skip_duplicates and Customer.objects.filter(mobile=mobile).exists():
            duplicates += 1
            continue

        valid += 1

        # Collect sample (first 5)
        if len(sample) < 5:
            sample.append(
                {
                    "row": i + 1,
                    "name": name,
                    "mobile": mobile,
                    "email": row.get(mapping.email_column or "", "").strip() if mapping.email_column else "",
                }
            )

    return {
        "total_rows": total,
        "valid_rows": valid,
        "duplicate_rows": duplicates,
        "invalid_rows": invalid,
        "sample_data": sample,
        "column_mapping": payload.column_mapping.model_dump(),
    }


@router.post("/import", response=CSVImportResponse)
def import_csv(request, payload: CSVImportRequest):
    """
    Import customers from CSV.
    """
    user = get_authenticated_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        csv_content = base64.b64decode(payload.file_content).decode("utf-8")
    except Exception as e:
        raise HttpError(400, f"Invalid file content: {e}")

    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    imported = 0
    duplicates = 0
    errors = []

    mapping = payload.column_mapping

    for i, row in enumerate(rows):
        try:
            name = row.get(mapping.name_column, "").strip()
            mobile = row.get(mapping.mobile_column, "").strip()

            if not name or not mobile:
                errors.append({"row": i + 1, "error": "Missing required fields"})
                continue

            # Check for duplicates
            if payload.skip_duplicates and Customer.objects.filter(mobile=mobile).exists():
                duplicates += 1
                continue

            # Create customer
            Customer.objects.create(
                name=name,
                mobile=mobile,
                email=row.get(mapping.email_column or "", "").strip() if mapping.email_column else "",
                nric=row.get(mapping.nric_column or "", "").strip() if mapping.nric_column else "",
                address=row.get(mapping.address_column or "", "").strip() if mapping.address_column else "",
                housing_type=row.get(mapping.housing_type_column or "", "").strip()
                if mapping.housing_type_column
                else "",
                pdpa_consent=row.get(mapping.pdpa_consent_column or "", "").strip().lower()
                in ["true", "yes", "1"]
                if mapping.pdpa_consent_column
                else False,
                entity_id=payload.entity_id,
                created_by=user,
            )
            imported += 1

        except Exception as e:
            errors.append({"row": i + 1, "error": str(e)})

    return {
        "imported_count": imported,
        "duplicate_count": duplicates,
        "error_count": len(errors),
        "errors": errors[:10],  # Limit errors returned
    }
