"""AVS Router — Phase 5: Sales Agreements & AVS Tracking."""

import logging
from typing import List
from uuid import UUID

from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import AuthenticationService
from apps.core.permissions import require_entity_access

from ..models import AVSStatus, AVSTransfer
from ..schemas import AVSTransferResponse
from ..services.avs import AVSService

logger = logging.getLogger(__name__)

router = Router(tags=["avs"])


@router.get("/avs/pending", response=List[AVSTransferResponse])
def list_pending_transfers(request, entity_id: UUID = None):
    """List pending AVS transfers."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    require_entity_access(request)

    if not user.has_role("management"):
        entity_id = user.entity_id

    transfers = AVSService.get_pending_transfers(entity_id)

    return [
        AVSTransferResponse(
            id=t.id,
            agreement_id=t.agreement_id,
            dog_id=t.dog_id,
            dog_name=t.dog.name,
            buyer_mobile=t.buyer_mobile,
            status=t.status,
            reminder_sent_at=t.reminder_sent_at,
            completed_at=t.completed_at,
            created_at=t.created_at,
        )
        for t in transfers
    ]


@router.get("/avs/{transfer_id}", response=AVSTransferResponse)
def get_transfer(request, transfer_id: UUID):
    """Get AVS transfer detail."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        transfer = AVSTransfer.objects.select_related("agreement", "dog").get(id=transfer_id)
    except AVSTransfer.DoesNotExist:
        raise HttpError(404, "Transfer not found")

    if not user.has_role("management") and transfer.agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    return AVSTransferResponse(
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


@router.post("/avs/{transfer_id}/complete", response=AVSTransferResponse)
def complete_transfer(request, transfer_id: UUID):
    """Mark AVS transfer as completed."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        transfer = AVSTransfer.objects.select_related("agreement", "dog").get(id=transfer_id)
    except AVSTransfer.DoesNotExist:
        raise HttpError(404, "Transfer not found")

    if not user.has_role("management") and transfer.agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    try:
        transfer = AVSService.mark_completed(str(transfer.token))
        return AVSTransferResponse(
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
    except Exception as e:
        logger.error(f"AVS completion failed: {e}")
        raise HttpError(400, str(e))


@router.get("/avs/{transfer_id}/link")
def get_transfer_link(request, transfer_id: UUID):
    """Get AVS transfer link for buyer."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        transfer = AVSTransfer.objects.select_related("agreement").get(id=transfer_id)
    except AVSTransfer.DoesNotExist:
        raise HttpError(404, "Transfer not found")

    if not user.has_role("management") and transfer.agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    link = AVSService.get_avs_link(transfer.token)

    return {
        "transfer_id": transfer_id,
        "token": transfer.token,
        "link": link,
        "status": transfer.status,
    }


@router.post("/avs/{transfer_id}/reminder")
async def send_reminder(request, transfer_id: UUID):
    """Send reminder for pending transfer."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        transfer = AVSTransfer.objects.select_related("agreement").get(id=transfer_id)
    except AVSTransfer.DoesNotExist:
        raise HttpError(404, "Transfer not found")

    if not user.has_role("management") and transfer.agreement.entity_id != user.entity_id:
        raise HttpError(403, "Access denied")

    if transfer.status != AVSStatus.SENT:
        raise HttpError(400, "Can only send reminder for SENT transfers")

    success = await AVSService.send_reminder(transfer)

    if success:
        return {"success": True, "message": "Reminder sent"}
    else:
        raise HttpError(500, "Failed to send reminder")


@router.post("/avs/{transfer_id}/escalate")
def escalate_transfer(request, transfer_id: UUID):
    """Escalate pending transfer to staff."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    require_entity_access(request)

    try:
        transfer = AVSTransfer.objects.select_related("agreement").get(id=transfer_id)
    except AVSTransfer.DoesNotExist:
        raise HttpError(404, "Transfer not found")

    if transfer.status != AVSStatus.SENT:
        raise HttpError(400, "Can only escalate SENT transfers")

    AVSService.escalate_to_staff(transfer)

    return {"success": True, "message": "Transfer escalated to staff"}


@router.get("/avs/check-reminders")
def check_reminders(request):
    """Check for transfers needing reminders."""
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")

    if not user.has_role("management"):
        raise HttpError(403, "Admin access required")

    transfers = AVSService.check_pending_reminders()

    return {
        "pending_reminders": len(transfers),
        "transfers": [
            {
                "id": str(t.id),
                "dog_name": t.dog.name,
                "buyer_mobile": t.buyer_mobile,
                "created_at": t.created_at.isoformat(),
            }
            for t in transfers
        ],
    }
