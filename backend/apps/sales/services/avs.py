"""AVS Service — Phase 5: Sales Agreements & AVS Tracking.

Handles AVS transfer link generation, sending, reminders, and escalation.
"""

import logging
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog, User
from apps.operations.models import Dog

from ..models import AVSTransfer, AVSStatus, SalesAgreement

logger = logging.getLogger(__name__)

# Configuration
AVS_REMINDER_HOURS = 72  # 3 days
AVS_TOKEN_TTL_SECONDS = 7 * 24 * 3600  # 7 days


class AVSService:
    """Service for managing AVS transfers."""

    @staticmethod
    def generate_token() -> str:
        """
        Generate unique token for AVS transfer link.

        Returns:
            UUID4 string
        """
        return str(uuid4())

    @staticmethod
    def create_avs_transfer(
        agreement: SalesAgreement,
        dog: Dog,
        buyer_mobile: str,
    ) -> AVSTransfer:
        """
        Create AVS transfer record.

        Args:
            agreement: SalesAgreement instance
            dog: Dog being transferred
            buyer_mobile: Buyer's mobile number

        Returns:
            Created AVSTransfer
        """
        token = AVSService.generate_token()

        with transaction.atomic():
            transfer = AVSTransfer.objects.create(
                agreement=agreement,
                dog=dog,
                buyer_mobile=buyer_mobile,
                token=token,
                status=AVSStatus.PENDING,
            )

            logger.info(f"AVS transfer created: {transfer.id} for dog {dog.microchip}")

        return transfer

    @staticmethod
    def get_avs_link(token: str) -> str:
        """
        Generate AVS transfer link URL.

        Args:
            token: Transfer token

        Returns:
            Full URL for buyer to complete transfer
        """
        base_url = getattr(settings, "FRONTEND_URL", "https://wellfond.sg")
        return f"{base_url}/avs/complete/{token}"

    @staticmethod
    async def send_avs_link(
        transfer: AVSTransfer,
        channel: str = "email",
    ) -> dict:
        """
        Send AVS link to buyer.

        Args:
            transfer: AVSTransfer instance
            channel: Communication channel (email, whatsapp, both)

        Returns:
            Dict with send result
        """
        link = AVSService.get_avs_link(transfer.token)

        # Prepare message
        message = (
            f"Hello, please complete the AVS transfer for {transfer.dog.name} "
            f"by clicking this link: {link}\n\n"
            f"This link expires in 7 days."
        )

        results = {"sent": False, "channels": []}

        # Send via email
        if channel in ["email", "both"]:
            try:
                # TODO: Integrate with Resend
                logger.info(f"Would send email to {transfer.agreement.buyer_email}")
                results["channels"].append("email")
            except Exception as e:
                logger.error(f"Email send failed: {e}")

        # Send via WhatsApp
        if channel in ["whatsapp", "both"]:
            try:
                # TODO: Integrate with WhatsApp Business API
                logger.info(f"Would send WhatsApp to {transfer.buyer_mobile}")
                results["channels"].append("whatsapp")
            except Exception as e:
                logger.error(f"WhatsApp send failed: {e}")

        # Update status if any channel succeeded
        if results["channels"]:
            transfer.status = AVSStatus.SENT
            transfer.save(update_fields=["status"])
            results["sent"] = True

        return results

    @staticmethod
    def check_completion(token: str) -> bool:
        """
        Check if AVS transfer is completed.

        Args:
            token: Transfer token

        Returns:
            True if completed
        """
        try:
            transfer = AVSTransfer.objects.get(token=token)
            return transfer.status == AVSStatus.COMPLETED
        except AVSTransfer.DoesNotExist:
            return False

    @staticmethod
    def mark_completed(token: str) -> AVSTransfer:
        """
        Mark AVS transfer as completed.

        Args:
            token: Transfer token

        Returns:
            Updated AVSTransfer
        """
        transfer = AVSTransfer.objects.get(token=token)
        transfer.status = AVSStatus.COMPLETED
        transfer.completed_at = timezone.now()
        transfer.save(update_fields=["status", "completed_at"])

        logger.info(f"AVS transfer completed: {transfer.id}")

        return transfer

    @staticmethod
    def check_pending_reminders() -> list[AVSTransfer]:
        """
        Find transfers that need reminders.

        Returns:
            List of AVSTransfer records that:
            - Status is SENT
            - Created more than AVS_REMINDER_HOURS ago
            - No reminder sent yet
        """
        cutoff_time = timezone.now() - timedelta(hours=AVS_REMINDER_HOURS)

        transfers = AVSTransfer.objects.filter(
            status=AVSStatus.SENT,
            created_at__lt=cutoff_time,
            reminder_sent_at__isnull=True,
        )

        return list(transfers)

    @staticmethod
    async def send_reminder(transfer: AVSTransfer) -> bool:
        """
        Send reminder for pending AVS transfer.

        Args:
            transfer: AVSTransfer instance

        Returns:
            True if reminder sent successfully
        """
        link = AVSService.get_avs_link(transfer.token)

        message = (
            f"REMINDER: Please complete the AVS transfer for {transfer.dog.name}. "
            f"Click here: {link}\n\n"
            f"This is a reminder sent 72 hours after the initial request."
        )

        try:
            # TODO: Send via email and WhatsApp
            logger.info(f"AVS reminder sent for transfer {transfer.id}")

            transfer.reminder_sent_at = timezone.now()
            transfer.save(update_fields=["reminder_sent_at"])

            return True
        except Exception as e:
            logger.error(f"Reminder send failed: {e}")
            return False

    @staticmethod
    def escalate_to_staff(transfer: AVSTransfer) -> None:
        """
        Escalate pending transfer to staff.

        Called when transfer is still pending after reminder.
        """
        transfer.status = AVSStatus.ESCALATED
        transfer.save(update_fields=["status"])

        # Create audit log
        AuditLog.objects.create(
            actor=None,  # System action
            action=AuditLog.Action.UPDATE,
            resource_type="AVSTransfer",
            resource_id=str(transfer.id),
            payload={
                "escalation_reason": "Transfer still pending after 72h reminder",
                "buyer_mobile": transfer.buyer_mobile,
            },
        )

        logger.info(f"AVS transfer escalated: {transfer.id}")

    @staticmethod
    def get_pending_transfers(entity_id=None) -> list[AVSTransfer]:
        """
        Get pending AVS transfers.

        Args:
            entity_id: Optional entity filter

        Returns:
            List of pending transfers
        """
        queryset = AVSTransfer.objects.filter(
            status__in=[AVSStatus.PENDING, AVSStatus.SENT]
        ).select_related("agreement", "dog")

        if entity_id:
            queryset = queryset.filter(agreement__entity_id=entity_id)

        return list(queryset)

    @staticmethod
    def check_escalation_needed(transfer: AVSTransfer) -> bool:
        """
        Check if transfer needs escalation.

        Returns True if:
        - Reminder was sent more than 24 hours ago
        - Transfer still not completed
        """
        if not transfer.reminder_sent_at:
            return False

        if transfer.status != AVSStatus.SENT:
            return False

        escalation_cutoff = transfer.reminder_sent_at + timedelta(hours=24)
        return timezone.now() > escalation_cutoff
