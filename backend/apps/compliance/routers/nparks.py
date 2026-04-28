"""NParks Router
===============
Phase 6: Compliance & NParks Reporting

Django Ninja router for NParks submission endpoints.
"""

import logging
from typing import List
from uuid import UUID

from django.http import HttpResponse
from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import AuthenticationService
from apps.core.permissions import require_entity_access, require_role

from ..models import NParksSubmission, NParksStatus
from ..schemas import (
    NParksGenerateRequest,
    NParksPreview,
    NParksSubmissionResponse,
    NParksListResponse,
)
from ..services.nparks import NParksService

logger = logging.getLogger(__name__)

router = Router(tags=["compliance", "nparks"])


@router.post("/generate", response=NParksSubmissionResponse)
def generate_npars(
    request,
    data: NParksGenerateRequest,
):
    """
    Generate all 5 NParks documents for entity+month.
    Creates DRAFT submission.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    require_entity_access(request)

    # Check user can generate for this entity
    if not user.has_role("management") and user.entity_id != data.entity_id:
        raise HttpError(403, "Access denied")

    try:
        documents = NParksService.generate_nparks(
            entity_id=data.entity_id,
            month=data.month,
            generated_by_id=user.id,
        )

        # Get the submission that was created
        submission = NParksSubmission.objects.get(
            entity_id=data.entity_id,
            month=data.month,
            status=NParksStatus.DRAFT,
        )

        return NParksSubmissionResponse.model_validate(submission)

    except Exception as e:
        logger.error(f"NParks generation failed: {e}")
        raise HttpError(400, str(e))


@router.get("/preview/{submission_id}", response=NParksPreview)
def preview_nparks(
    request,
    submission_id: UUID,
    doc_type: str,  # Query param
):
    """
    Preview NParks document data before download.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        submission = NParksSubmission.objects.get(id=submission_id)
    except NParksSubmission.DoesNotExist:
        raise HttpError(404, "Submission not found")

    # Check access
    if not user.has_role("management") and submission.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    try:
        preview = NParksService.preview_nparks(
            entity_id=submission.entity_id,
            month=submission.month,
            doc_type=doc_type,
        )
        return preview

    except Exception as e:
        logger.error(f"NParks preview failed: {e}")
        raise HttpError(400, str(e))


@router.post("/submit/{submission_id}", response=NParksSubmissionResponse)
def submit_nparks(
    request,
    submission_id: UUID,
):
    """
    Submit NParks documents (mark as SUBMITTED).
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        submission = NParksSubmission.objects.get(id=submission_id)
    except NParksSubmission.DoesNotExist:
        raise HttpError(404, "Submission not found")

    # Check access
    if not user.has_role("management") and submission.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    # Check status
    if submission.status != NParksStatus.DRAFT:
        raise HttpError(400, f"Cannot submit - status is {submission.status}")

    # Update status
    from django.utils import timezone

    submission.status = NParksStatus.SUBMITTED
    submission.submitted_at = timezone.now()
    submission.save(update_fields=["status", "submitted_at", "updated_at"])

    logger.info(f"NParks submission {submission_id} submitted by {user.email}")

    return NParksSubmissionResponse.model_validate(submission)


@router.post("/lock/{submission_id}", response=NParksSubmissionResponse)
def lock_nparks(
    request,
    submission_id: UUID,
):
    """
    Lock NParks submission (irreversible).
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    require_role(request, "management", "admin")

    try:
        submission = NParksSubmission.objects.get(id=submission_id)
    except NParksSubmission.DoesNotExist:
        raise HttpError(404, "Submission not found")

    # Check status
    if submission.status == NParksStatus.LOCKED:
        raise HttpError(400, "Already locked")

    if submission.status != NParksStatus.SUBMITTED:
        raise HttpError(400, f"Cannot lock - status is {submission.status} (must be SUBMITTED)")

    # Update status
    from django.utils import timezone

    submission.status = NParksStatus.LOCKED
    submission.locked_at = timezone.now()
    submission.save(update_fields=["status", "locked_at", "updated_at"])

    logger.info(f"NParks submission {submission_id} locked by {user.email}")

    return NParksSubmissionResponse.model_validate(submission)


@router.get("/download/{submission_id}")
def download_nparks(
    request,
    submission_id: UUID,
    doc_type: str,  # Query param: mating_sheet, puppy_movement, vet_treatments, puppies_bred, dog_movement
):
    """
    Download NParks Excel document.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        submission = NParksSubmission.objects.get(id=submission_id)
    except NParksSubmission.DoesNotExist:
        raise HttpError(404, "Submission not found")

    # Check access
    if not user.has_role("management") and submission.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    # Validate doc_type
    valid_types = ["mating_sheet", "puppy_movement", "vet_treatments", "puppies_bred", "dog_movement"]
    if doc_type not in valid_types:
        raise HttpError(400, f"Invalid doc_type. Must be one of: {', '.join(valid_types)}")

    try:
        # Regenerate the document (for now, we regenerate on download)
        # In production, we'd store the files and retrieve them
        from ..services.nparks import NParksService

        documents = NParksService.generate_nparks(
            entity_id=submission.entity_id,
            month=submission.month,
            generated_by_id=user.id,
        )

        excel_bytes = documents.get(doc_type)
        if not excel_bytes:
            raise HttpError(404, "Document not found")

        # Build filename
        entity_code = submission.entity.code.lower()
        month_str = submission.month.strftime("%Y%m")
        filename = f"nparks_{doc_type}_{entity_code}_{month_str}.xlsx"

        response = HttpResponse(
            excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"NParks download failed: {e}")
        raise HttpError(400, str(e))


@router.get("/", response=NParksListResponse)
def list_nparks(
    request,
    entity_id: UUID = None,
    page: int = 1,
    per_page: int = 25,
):
    """
    List NParks submissions.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Build queryset
    queryset = NParksSubmission.objects.select_related("entity", "generated_by")

    # Entity filter
    if entity_id:
        if not user.has_role("management") and user.entity_id != entity_id:
            raise HttpError(403, "Access denied")
        queryset = queryset.filter(entity_id=entity_id)
    elif not user.has_role("management"):
        queryset = queryset.filter(entity_id=user.entity_id)

    # Order by month descending
    queryset = queryset.order_by("-month")

    # Pagination
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    items = list(queryset[start:end])

    return NParksListResponse(
        items=[NParksSubmissionResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{submission_id}/validate")
def validate_nparks(
    request,
    submission_id: UUID,
):
    """
    Validate NParks submission requirements.
    Returns list of warnings.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        submission = NParksSubmission.objects.get(id=submission_id)
    except NParksSubmission.DoesNotExist:
        raise HttpError(404, "Submission not found")

    # Check access
    if not user.has_role("management") and submission.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    # Validate
    warnings = NParksService.validate_nparks(
        entity_id=submission.entity_id,
        month=submission.month,
    )

    return {
        "submission_id": str(submission_id),
        "warnings": warnings,
        "is_valid": len(warnings) == 0,
    }
