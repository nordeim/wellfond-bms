"""Celery Tasks — Phase 5: Sales Agreements & AVS Tracking."""

import logging
from decimal import Decimal

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.cache import cache
from django.utils import timezone

from apps.core.models import AuditLog

from .models import AVSStatus, AVSTransfer, SalesAgreement
from .services.avs import AVSService
from .services.pdf import PDFService

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 60  # 60 seconds initial backoff


@shared_task(
    queue="default",
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_BACKOFF,
)
def send_agreement_pdf(self, agreement_id: str, channel: str = "email"):
    """
    Send agreement PDF to buyer.

    Args:
        agreement_id: Agreement UUID string
        channel: Communication channel (email, whatsapp, both)

    Returns:
        Dict with send result
    """
    import asyncio

    try:
        agreement = SalesAgreement.objects.select_related("entity").get(
            id=agreement_id
        )
    except SalesAgreement.DoesNotExist:
        logger.error(f"Agreement not found: {agreement_id}")
        return {"error": "Agreement not found"}

    try:
        # Generate PDF
        pdf_bytes, pdf_hash = asyncio.run(
            PDFService.render_agreement_pdf(
                agreement_id=agreement.id,
                watermark=False,
            )
        )

        # Store hash
        agreement.pdf_hash = pdf_hash
        agreement.save(update_fields=["pdf_hash"])

        # TODO: Send email via Resend
        # TODO: Send WhatsApp via Business API

        logger.info(
            f"Agreement PDF sent: {agreement_id} via {channel} (hash: {pdf_hash})"
        )

        # Log to audit
        AuditLog.objects.create(
            actor=None,  # System action
            action=AuditLog.Action.UPDATE,
            resource_type="SalesAgreement",
            resource_id=str(agreement_id),
            payload={
                "action": "pdf_sent",
                "channel": channel,
                "pdf_hash": pdf_hash,
            },
        )

        return {
            "success": True,
            "agreement_id": agreement_id,
            "pdf_hash": pdf_hash,
            "channel": channel,
        }

    except Exception as exc:
        logger.error(f"PDF send failed: {exc}")

        if self.request.retries < MAX_RETRIES:
            logger.info(f"Retrying send_agreement_pdf ({self.request.retries + 1}/{MAX_RETRIES})")
            raise self.retry(exc=exc)
        else:
            logger.error(f"Max retries exceeded for agreement {agreement_id}")
            raise MaxRetriesExceededError(f"Failed to send PDF for {agreement_id}")


@shared_task(
    queue="default",
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_BACKOFF,
)
def send_avs_reminder(self, transfer_id: str):
    """
    Send AVS reminder to buyer.

    Args:
        transfer_id: AVSTransfer UUID string

    Returns:
        Dict with send result
    """
    import asyncio

    try:
        transfer = AVSTransfer.objects.select_related("agreement", "dog").get(
            id=transfer_id
        )
    except AVSTransfer.DoesNotExist:
        logger.error(f"Transfer not found: {transfer_id}")
        return {"error": "Transfer not found"}

    if transfer.status != AVSStatus.SENT:
        logger.info(f"Skipping reminder for transfer {transfer_id}: status is {transfer.status}")
        return {"skipped": True, "reason": f"Status is {transfer.status}"}

    try:
        success = asyncio.run(AVSService.send_reminder(transfer))

        if success:
            logger.info(f"AVS reminder sent: {transfer_id}")
            return {"success": True, "transfer_id": transfer_id}
        else:
            logger.error(f"AVS reminder failed: {transfer_id}")
            raise Exception("Reminder send failed")

    except Exception as exc:
        logger.error(f"AVS reminder error: {exc}")

        if self.request.retries < MAX_RETRIES:
            raise self.retry(exc=exc)
        else:
            logger.error(f"Max retries exceeded for transfer {transfer_id}")
            raise MaxRetriesExceededError(f"Failed to send reminder for {transfer_id}")


@shared_task(queue="low")
def check_avs_reminders():
    """
    Check for pending AVS reminders.

    Scheduled via Celery Beat daily at 9am SGT.
    Finds transfers needing reminders and escalations.
    """
    import asyncio

    logger.info("Running AVS reminder check")

    # Get transfers needing reminders
    pending = AVSService.check_pending_reminders()
    logger.info(f"Found {len(pending)} transfers needing reminders")

    reminder_count = 0
    escalation_count = 0

    for transfer in pending:
        # Send reminder
        try:
            success = asyncio.run(AVSService.send_reminder(transfer))
            if success:
                reminder_count += 1
        except Exception as e:
            logger.error(f"Reminder failed for {transfer.id}: {e}")

    # Check for escalations
    escalations = AVSTransfer.objects.filter(
        status=AVSStatus.SENT,
        reminder_sent_at__isnull=False,
    )

    for transfer in escalations:
        if AVSService.check_escalation_needed(transfer):
            AVSService.escalate_to_staff(transfer)
            escalation_count += 1
            logger.info(f"Escalated transfer: {transfer.id}")

    logger.info(
        f"AVS reminder check complete: {reminder_count} reminders, {escalation_count} escalations"
    )

    return {
        "reminders_sent": reminder_count,
        "escalations": escalation_count,
        "checked_at": timezone.now().isoformat(),
    }


@shared_task(queue="low")
def cleanup_expired_avs_tokens():
    """
    Clean up expired AVS tokens.

    Removes transfers older than 30 days that were never completed.
    """
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=30)

    expired = AVSTransfer.objects.filter(
        status__in=[AVSStatus.PENDING, AVSStatus.SENT],
        created_at__lt=cutoff,
    )

    count = expired.count()
    expired.delete()

    logger.info(f"Cleaned up {count} expired AVS transfers")

    return {"cleaned": count}
