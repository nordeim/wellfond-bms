"""Agreements Router — Phase 5: Sales Agreements & AVS Tracking."""

import logging
from typing import List
from uuid import UUID

from django.db import IntegrityError
from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import AuthenticationService
from apps.core.models import AuditLog
from apps.core.permissions import require_entity_access, require_role
from apps.operations.models import Dog

from ..models import AgreementStatus, SalesAgreement, SignatureMethod, SignerType
from ..schemas import (
    AgreementCreate,
    AgreementDetail,
    AgreementFilters,
    AgreementListItem,
    AgreementSendResponse,
    AgreementUpdate,
    LineItemResponse,
    PaginatedAgreements,
    SendAgreementRequest,
    SignAgreementRequest,
    SignatureResponse,
)
from ..services.agreement import AgreementService
from ..services.avs import AVSService
from ..services.pdf import PDFService

logger = logging.getLogger(__name__)

router = Router(tags=["sales"])


@router.post("/agreements", response=AgreementDetail)
def create_agreement(request, data: AgreementCreate):
    """
    Create a new sales agreement.

    Creates draft agreement with buyer info, dogs, and pricing.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    require_entity_access(request)

    try:
        agreement = AgreementService.create_agreement(
            type=data.type,
            entity_id=data.entity_id,
            dog_ids=[str(d) for d in data.dog_ids],
            buyer_info={
                "name": data.buyer_info.name,
                "nric": data.buyer_info.nric,
                "mobile": data.buyer_info.mobile,
                "email": data.buyer_info.email,
                "address": data.buyer_info.address,
                "housing_type": data.buyer_info.housing_type,
            },
            pricing=data.pricing,
            created_by=user,
            special_conditions=data.special_conditions,
            pdpa_consent=data.pdpa_consent,
        )

        return _build_agreement_detail(agreement)

    except Exception as e:
        logger.error(f"Agreement creation failed: {e}")
        raise HttpError(400, str(e))


@router.get("/agreements", response=PaginatedAgreements)
def list_agreements(
    request,
    type: str = None,
    status: str = None,
    entity_id: UUID = None,
    date_from: str = None,
    date_to: str = None,
    buyer_mobile: str = None,
    page: int = 1,
    per_page: int = 25,
):
    """
    List agreements with filters.

    Returns paginated list scoped to user's entity.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # Build queryset
    queryset = SalesAgreement.objects.select_related(
        "entity", "created_by"
    ).prefetch_related("line_items__dog")

    # Apply entity scoping
    if not user.has_role("management"):
        queryset = queryset.filter(entity_id=user.entity_id)
    elif entity_id:
        queryset = queryset.filter(entity_id=entity_id)

    # Apply filters
    if type:
        queryset = queryset.filter(type=type)
    if status:
        queryset = queryset.filter(status=status)
    if buyer_mobile:
        queryset = queryset.filter(buyer_mobile__icontains=buyer_mobile)
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    # Order by created_at desc
    queryset = queryset.order_by("-created_at")

    # Manual pagination
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    page_qs = queryset[start:end]

    # Build response
    agreements = []
    for agreement in page_qs:
        agreements.append(_build_list_item(agreement))

    return {
        "agreements": agreements,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/agreements/{agreement_id}", response=AgreementDetail)
def get_agreement(request, agreement_id: UUID):
    """
    Get agreement detail.

    Returns full agreement with line items, signatures, AVS status.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        agreement = SalesAgreement.objects.select_related(
            "entity", "created_by"
        ).prefetch_related(
            "line_items__dog", "signatures", "avs_transfers"
        ).get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        raise HttpError(404, "Agreement not found")

    # Entity scoping
    if not user.has_role("management") and agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    return _build_agreement_detail(agreement)


@router.patch("/agreements/{agreement_id}", response=AgreementDetail)
def update_agreement(request, agreement_id: UUID, data: AgreementUpdate):
    """
    Update draft agreement.

    Only draft agreements can be updated.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        agreement = SalesAgreement.objects.get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        raise HttpError(404, "Agreement not found")

    # Entity scoping
    if not user.has_role("management") and agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    if agreement.status != AgreementStatus.DRAFT:
        raise HttpError(400, "Only draft agreements can be updated")

    try:
        buyer_info = None
        if data.buyer_info:
            buyer_info = {
                "name": data.buyer_info.name,
                "nric": data.buyer_info.nric,
                "mobile": data.buyer_info.mobile,
                "email": data.buyer_info.email,
                "address": data.buyer_info.address,
                "housing_type": data.buyer_info.housing_type,
            }

        agreement = AgreementService.update_agreement(
            agreement=agreement,
            user=user,
            buyer_info=buyer_info,
            pricing=data.pricing,
            special_conditions=data.special_conditions,
            pdpa_consent=data.pdpa_consent,
        )

        return _build_agreement_detail(agreement)

    except Exception as e:
        logger.error(f"Agreement update failed: {e}")
        raise HttpError(400, str(e))


@router.post("/agreements/{agreement_id}/sign", response=AgreementDetail)
def sign_agreement(request, agreement_id: UUID, data: SignAgreementRequest):
    """
    Capture signature on agreement.

    Transitions agreement from DRAFT to SIGNED.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        agreement = SalesAgreement.objects.get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        raise HttpError(404, "Agreement not found")

    # Entity scoping
    if not user.has_role("management") and agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    try:
        # Create signature
        from ..models import Signature

        sig_data = data.signature
        signature = Signature.objects.create(
            agreement=agreement,
            signer_type=SignerType.SELLER,
            method=sig_data.method,
            coordinates=[c.model_dump() for c in (sig_data.coordinates or [])],
            ip_address=request.META.get("REMOTE_ADDR"),
            image_url=sig_data.image_url or "",
        )

        # Transition to SIGNED
        agreement = AgreementService.transition(
            agreement=agreement,
            new_status=AgreementStatus.SIGNED,
            user=user,
        )

        return _build_agreement_detail(agreement)

    except Exception as e:
        logger.error(f"Agreement signing failed: {e}")
        raise HttpError(400, str(e))


@router.post("/agreements/{agreement_id}/send", response=AgreementSendResponse)
async def send_agreement(
    request, agreement_id: UUID, data: SendAgreementRequest
):
    """
    Send agreement to buyer.

    Generates PDF, creates AVS transfers, dispatches via email/WhatsApp.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        agreement = SalesAgreement.objects.select_related(
            "entity"
        ).prefetch_related("line_items__dog").get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        raise HttpError(404, "Agreement not found")

    # Entity scoping
    if not user.has_role("management") and agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    if agreement.status != AgreementStatus.SIGNED:
        raise HttpError(400, "Agreement must be signed before sending")

    try:
        # Generate PDF
        import asyncio

        pdf_bytes, pdf_hash = await PDFService.render_agreement_pdf(
            agreement_id=agreement.id,
            watermark=False,
        )

        # Store PDF hash
        agreement.pdf_hash = pdf_hash
        agreement.pdf_url = f"/media/agreements/{agreement.id}.pdf"
        agreement.save(update_fields=["pdf_hash", "pdf_url"])

        # Create AVS transfers for each dog
        avs_tokens = []
        for item in agreement.line_items.all():
            transfer = AVSService.create_avs_transfer(
                agreement=agreement,
                dog=item.dog,
                buyer_mobile=agreement.buyer_mobile,
            )
            avs_tokens.append(transfer.token)

        # Send via selected channel
        # TODO: Integrate with actual email/WhatsApp services
        channel = data.channel
        logger.info(f"Sending agreement {agreement_id} via {channel}")

        # Transition to COMPLETED
        agreement = AgreementService.transition(
            agreement=agreement,
            new_status=AgreementStatus.COMPLETED,
            user=user,
        )

        return {
            "success": True,
            "message": f"Agreement sent via {channel}",
            "pdf_url": agreement.pdf_url,
            "avs_token": avs_tokens[0] if avs_tokens else None,
        }

    except Exception as e:
        logger.error(f"Agreement send failed: {e}")
        raise HttpError(500, str(e))


@router.delete("/agreements/{agreement_id}")
def cancel_agreement(request, agreement_id: UUID, reason: str = ""):
    """
    Cancel agreement.

    Only draft or signed agreements can be cancelled.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        agreement = SalesAgreement.objects.get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        raise HttpError(404, "Agreement not found")

    # Entity scoping
    if not user.has_role("management") and agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    if agreement.status not in [AgreementStatus.DRAFT, AgreementStatus.SIGNED]:
        raise HttpError(400, "Cannot cancel agreement in current status")

    try:
        agreement = AgreementService.transition(
            agreement=agreement,
            new_status=AgreementStatus.CANCELLED,
            user=user,
            reason=reason,
        )

        return {"success": True, "message": "Agreement cancelled"}

    except Exception as e:
        logger.error(f"Agreement cancellation failed: {e}")
        raise HttpError(400, str(e))


@router.get("/agreements/{agreement_id}/hdb-warning")
def check_hdb_warning(request, agreement_id: UUID):
    """
    Check if HDB warning applies to agreement.

    Returns warning if buyer has HDB housing and dogs include large breeds.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        agreement = SalesAgreement.objects.prefetch_related(
            "line_items__dog"
        ).get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        raise HttpError(404, "Agreement not found")

    # Entity scoping
    if not user.has_role("management") and agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    warning = AgreementService.check_hdb_warning(agreement)

    return warning or {"warning": False}


# =============================================================================
# Helper Functions
# =============================================================================


def _build_list_item(agreement: SalesAgreement) -> dict:
    """Build AgreementListItem from model."""
    line_items = []
    for item in agreement.line_items.all():
        line_items.append(
            LineItemResponse(
                id=item.id,
                dog_id=item.dog_id,
                dog_name=item.dog.name,
                dog_microchip=item.dog.microchip,
                price=item.price,
                gst_component=item.gst_component,
            )
        )

    return {
        "id": agreement.id,
        "type": agreement.type,
        "status": agreement.status,
        "buyer_name": agreement.buyer_name,
        "buyer_mobile": agreement.buyer_mobile,
        "entity_id": agreement.entity_id,
        "entity_name": agreement.entity.name,
        "total_amount": agreement.total_amount,
        "deposit": agreement.deposit,
        "pdf_hash": agreement.pdf_hash,
        "signed_at": agreement.signed_at,
        "created_at": agreement.created_at,
        "line_items": line_items,
    }


def _build_agreement_detail(agreement: SalesAgreement) -> dict:
    """Build AgreementDetail from model."""
    # Build line items
    line_items = []
    for item in agreement.line_items.all():
        line_items.append(
            LineItemResponse(
                id=item.id,
                dog_id=item.dog_id,
                dog_name=item.dog.name,
                dog_microchip=item.dog.microchip,
                price=item.price,
                gst_component=item.gst_component,
            )
        )

    # Build signatures
    signatures = []
    for sig in agreement.signatures.all():
        signatures.append(
            SignatureResponse(
                id=sig.id,
                signer_type=sig.signer_type,
                method=sig.method,
                coordinates=sig.coordinates,
                ip_address=sig.ip_address,
                timestamp=sig.timestamp,
                image_url=sig.image_url,
            )
        )

    # Build AVS transfers
    from ..schemas import AVSTransferResponse

    avs_transfers = []
    for transfer in agreement.avs_transfers.all():
        avs_transfers.append(
            AVSTransferResponse(
                id=transfer.id,
                agreement_id=transfer.agreement_id,
                dog_id=transfer.dog_id,
                dog_name=transfer.dog.name,
                buyer_mobile=transfer.buyer_mobile,
                status=transfer.status,
                reminder_sent_at=transfer.reminder_sent_at,
                completed_at=transfer.completed_at,
                created_at=transfer.created_at,
            )
        )

    return {
        "id": agreement.id,
        "type": agreement.type,
        "status": agreement.status,
        "entity_id": agreement.entity_id,
        "entity_name": agreement.entity.name,
        "buyer_name": agreement.buyer_name,
        "buyer_nric": agreement.buyer_nric,
        "buyer_mobile": agreement.buyer_mobile,
        "buyer_email": agreement.buyer_email,
        "buyer_address": agreement.buyer_address,
        "buyer_housing_type": agreement.buyer_housing_type,
        "pdpa_consent": agreement.pdpa_consent,
        "total_amount": agreement.total_amount,
        "gst_component": agreement.gst_component,
        "deposit": agreement.deposit,
        "balance": agreement.balance,
        "payment_method": agreement.payment_method,
        "special_conditions": agreement.special_conditions,
        "pdf_hash": agreement.pdf_hash,
        "pdf_url": agreement.pdf_url,
        "signed_at": agreement.signed_at,
        "signatures": signatures,
        "avs_transfers": avs_transfers,
        "line_items": line_items,
        "created_by": agreement.created_by.get_full_name() or agreement.created_by.email,
        "created_at": agreement.created_at,
    }
