"""Blast Service
===============
Phase 7: Customer DB & Marketing Blast

Marketing blast dispatch with Resend email and WhatsApp Business API.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Optional
from uuid import UUID

from django.db import transaction

from apps.core.models import User
from ..models import CommunicationChannel, CommunicationLog, Customer
from ..schemas import BlastCreate, BlastResult

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate_per_second: float = 10.0):
        self.rate = rate_per_second
        self.tokens = rate_per_second
        self.last_update = time.time()

    def acquire(self) -> bool:
        """
        Acquire a token. Returns True if allowed, False if rate limited.
        """
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class BlastProgressTracker:
    """Track blast progress via Redis."""

    def __init__(self, blast_id: UUID):
        self.blast_id = blast_id
        self.redis_key = f"blast:{blast_id}:progress"

    def init_progress(self, total: int):
        """Initialize progress tracking."""
        from django.core.cache import cache

        cache.set(
            self.redis_key,
            json.dumps({
                "total": total,
                "sent": 0,
                "delivered": 0,
                "failed": 0,
                "in_progress": True,
                "percentage": 0,
            }),
            timeout=3600,  # 1 hour
        )
        logger.info(f"Blast {self.blast_id} initialized with {total} recipients")

    def update_progress(self, sent: int, delivered: int, failed: int):
        """Update progress."""
        from django.core.cache import cache

        data = cache.get(self.redis_key)
        if data:
            progress = json.loads(data)
            progress["sent"] = sent
            progress["delivered"] = delivered
            progress["failed"] = failed
            progress["percentage"] = int((sent / progress["total"]) * 100) if progress["total"] > 0 else 0
            cache.set(self.redis_key, json.dumps(progress), timeout=3600)

    def complete(self):
        """Mark blast as complete."""
        from django.core.cache import cache

        data = cache.get(self.redis_key)
        if data:
            progress = json.loads(data)
            progress["in_progress"] = False
            progress["percentage"] = 100
            cache.set(self.redis_key, json.dumps(progress), timeout=3600)

    def get_progress(self) -> dict:
        """Get current progress."""
        from django.core.cache import cache

        data = cache.get(self.redis_key)
        if data:
            return json.loads(data)
        return {
            "total": 0,
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "in_progress": False,
            "percentage": 0,
        }


class BlastService:
    """Service for sending marketing blasts."""

    RATE_LIMIT = 10.0  # 10 per second
    CHUNK_SIZE = 50  # 50 customers per chunk

    # Token bucket for rate limiting
    _rate_limiter = RateLimiter(RATE_LIMIT)

    @staticmethod
    def get_recipients(payload: BlastCreate) -> list[Customer]:
        """
        Get recipient list from segment or customer_ids.

        Args:
            payload: Blast configuration

        Returns:
            List of customer objects
        """
        from .segmentation import SegmentationService

        if payload.segment_id:
            queryset = SegmentationService.get_segment_customers(payload.segment_id)
            return list(queryset)

        if payload.customer_ids:
            return list(Customer.objects.filter(id__in=payload.customer_ids))

        return []

    @staticmethod
    def apply_merge_tags(message: str, customer: Customer, merge_tags: dict) -> str:
        """
        Apply merge tags to message template.

        Supported tags:
        - {{name}} - Customer name
        - {{mobile}} - Customer mobile
        - {{entity}} - Entity name
        - {{breed}} - Placeholder for purchased breed
        - {{email}} - Customer email

        Args:
            message: Template message
            customer: Customer to personalize for
            merge_tags: Additional custom tags

        Returns:
            Personalized message
        """
        result = message

        # Standard tags
        replacements = {
            "{{name}}": customer.name,
            "{{mobile}}": customer.mobile,
            "{{entity}}": customer.entity.name if customer.entity else "",
            "{{email}}": customer.email or "",
            "{{breed}}": merge_tags.get("breed", ""),  # Would need purchase history
            "{{housing}}": customer.housing_type or "",
        }

        for tag, value in replacements.items():
            result = result.replace(tag, str(value))

        # Custom merge tags
        for tag, value in merge_tags.items():
            result = result.replace(f"{{{{{tag}}}}}", str(value))

        return result

    @staticmethod
    def send_blast(blast_id: UUID, payload: BlastCreate, actor: User) -> BlastResult:
        """
        Send marketing blast to recipients.

        Args:
            blast_id: Blast UUID
            payload: Blast configuration
            actor: User initiating the blast

        Returns:
            BlastResult with status
        """
        from ..tasks import dispatch_blast

        recipients = BlastService.get_recipients(payload)
        total = len(recipients)

        if total == 0:
            return BlastResult(
                blast_id=blast_id,
                total_recipients=0,
                eligible_recipients=0,
                excluded_count=0,
                channel=str(payload.channel.value if hasattr(payload.channel, "value") else payload.channel),
                status="NO_RECIPIENTS",
                started_at=datetime.now(),
            )

        # Apply PDPA filter
        eligible = [r for r in recipients if r.pdpa_consent]
        excluded = total - len(eligible)

        # Log excluded customers
        if excluded > 0:
            logger.info(f"Blast {blast_id}: {excluded} customers excluded (PDPA opt-out)")

        # Initialize progress tracking
        tracker = BlastProgressTracker(blast_id)
        tracker.init_progress(len(eligible))

        # Queue Celery task for chunked dispatch
        dispatch_blast.delay(
            str(blast_id),
            [str(c.id) for c in eligible],
            str(payload.channel.value if hasattr(payload.channel, "value") else payload.channel),
            payload.body,
            payload.subject or "",
            payload.merge_tags or {},
            str(actor.id),
        )

        return BlastResult(
            blast_id=blast_id,
            total_recipients=total,
            eligible_recipients=len(eligible),
            excluded_count=excluded,
            channel=str(payload.channel.value if hasattr(payload.channel, "value") else payload.channel),
            status="QUEUED",
            started_at=datetime.now(),
        )

    @staticmethod
    def send_email(
        customer: Customer,
        subject: str,
        body: str,
        blast_id: Optional[UUID] = None,
    ) -> dict:
        """
        Send email via Resend SDK.

        PLACEHOLDER: Replace with actual Resend SDK integration
        https://resend.com/docs/api-reference/emails/send-email

        Args:
            customer: Customer to email
            subject: Email subject
            body: HTML email body
            blast_id: Optional blast ID for tracking

        Returns:
            Dict with status and external_id
        """
        # Validate rate limit
        if not BlastService._rate_limiter.acquire():
            logger.warning(f"Rate limit hit for email to {customer.email}")
            return {"status": "RATE_LIMITED", "error": "Rate limit exceeded"}

        # PLACEHOLDER: Replace with actual Resend SDK call
        # import resend
        # resend.api_key = settings.RESEND_API_KEY
        # response = resend.Emails.send({
        #     "from": "marketing@wellfond.sg",
        #     "to": customer.email,
        #     "subject": subject,
        #     "html": body,
        # })

        # Simulated response for now
        logger.info(f"EMAIL [PLACEHOLDER] to {customer.email}: {subject[:50]}...")

        return {
            "status": "SENT",
            "external_id": f"resend_placeholder_{customer.id}",
        }

    @staticmethod
    def send_whatsapp(
        customer: Customer,
        body: str,
        blast_id: Optional[UUID] = None,
    ) -> dict:
        """
        Send WhatsApp via Business Cloud API.

        PLACEHOLDER: Replace with actual WhatsApp Business SDK integration
        https://developers.facebook.com/docs/whatsapp/cloud-api

        Args:
            customer: Customer to message
            body: Message body
            blast_id: Optional blast ID for tracking

        Returns:
            Dict with status and external_id
        """
        # Validate rate limit
        if not BlastService._rate_limiter.acquire():
            logger.warning(f"Rate limit hit for WA to {customer.mobile}")
            return {"status": "RATE_LIMITED", "error": "Rate limit exceeded"}

        # PLACEHOLDER: Replace with actual WhatsApp API call
        # Would use requests.post to:
        # https://graph.facebook.com/v18.0/{phone_number_id}/messages
        # with authentication and proper formatting

        # Simulated response for now
        logger.info(f"WHATSAPP [PLACEHOLDER] to {customer.mobile}: {body[:50]}...")

        return {
            "status": "SENT",
            "external_id": f"wa_placeholder_{customer.id}",
        }

    @staticmethod
    def log_communication(
        customer: Customer,
        channel: str,
        status: str,
        message_preview: str,
        subject: str = "",
        blast_id: Optional[UUID] = None,
        external_id: str = "",
        error_message: str = "",
    ) -> CommunicationLog:
        """Log communication attempt."""
        # Prepare timestamp fields before create
        sent_at = None
        delivered_at = None
        if status in ["SENT", "DELIVERED"]:
            sent_at = datetime.now()
        if status == "DELIVERED":
            delivered_at = datetime.now()

        # Create log with all fields (single atomic save)
        with transaction.atomic():
            log = CommunicationLog.objects.create(
                customer=customer,
                blast_id=blast_id,
                channel=channel,
                status=status,
                subject=subject,
                message_preview=message_preview[:200],
                external_id=external_id,
                error_message=error_message,
                sent_at=sent_at,
                delivered_at=delivered_at,
            )

        logger.info(f"Logged {channel} {status} for {customer.id}")
        return log

    @staticmethod
    def handle_bounce(customer: Customer, external_id: str, reason: str):
        """
        Handle bounced message.

        Args:
            customer: Customer
            external_id: External provider ID
            reason: Bounce reason
        """
        try:
            log = CommunicationLog.objects.get(
                external_id=external_id,
                customer=customer,
            )
            log.status = "BOUNCED"
            log.error_message = reason
            log.save()
            logger.warning(f"Bounced: {external_id} - {reason}")
        except CommunicationLog.DoesNotExist:
            logger.error(f"Bounce for unknown message: {external_id}")

    @staticmethod
    def handle_webhook(provider: str, payload: dict):
        """
        Handle webhook from email/WA provider.

        Args:
            provider: "resend" or "whatsapp"
            payload: Webhook payload
        """
        event = payload.get("type", payload.get("event", "unknown"))

        if provider == "resend":
            message_id = payload.get("data", {}).get("id", "")
            email = payload.get("data", {}).get("to", [""])[0]

            if event == "email.delivered":
                # Update status to DELIVERED
                logger.info(f"Resend delivered: {message_id}")
            elif event == "email.bounced":
                reason = payload.get("data", {}).get("bounce", {}).get("message", "")
                logger.warning(f"Resend bounced: {message_id} - {reason}")

        elif provider == "whatsapp":
            # Handle WhatsApp webhooks
            status = payload.get("status", "")
            message_id = payload.get("messages", [{}])[0].get("id", "")

            if status == "delivered":
                logger.info(f"WA delivered: {message_id}")
            elif status == "failed":
                error = payload.get("errors", [{}])[0].get("code", "")
                logger.warning(f"WA failed: {message_id} - {error}")


class CommunicationRouter:
    """Route messages with fallback logic."""

    @staticmethod
    def route_message(
        customer: Customer,
        channel: str,
        subject: str,
        body: str,
        blast_id: Optional[UUID] = None,
    ) -> dict:
        """
        Route message with fallback to email on WA failure.

        Args:
            customer: Customer to send to
            channel: EMAIL, WA, or BOTH
            subject: Email subject
            body: Message body
            blast_id: Blast ID

        Returns:
            Dict with status, channel_used, and details
        """
        result = {
            "status": "PENDING",
            "channel_used": None,
            "error": None,
            "fallback": False,
        }

        if channel in ["BOTH", "WA"]:
            # Try WhatsApp first if channel is BOTH or WA
            wa_result = BlastService.send_whatsapp(customer, body, blast_id)

            if wa_result["status"] == "SENT":
                result["status"] = "SENT"
                result["channel_used"] = "WA"
                result["external_id"] = wa_result.get("external_id", "")
                BlastService.log_communication(
                    customer,
                    "WA",
                    "SENT",
                    body,
                    "",
                    blast_id,
                    wa_result.get("external_id", ""),
                )
                return result

            # WA failed, fallback to email if BOTH
            if channel == "BOTH":
                result["fallback"] = True
                result["error"] = f"WA failed: {wa_result.get('error', 'Unknown')}"
                logger.info(f"Falling back to email for {customer.id}")

        if channel in ["BOTH", "EMAIL"]:
            # Send email
            email_result = BlastService.send_email(
                customer, subject, body, blast_id
            )

            if email_result["status"] == "SENT":
                result["status"] = "SENT"
                result["channel_used"] = "EMAIL"
                result["external_id"] = email_result.get("external_id", "")
                BlastService.log_communication(
                    customer,
                    "EMAIL",
                    "SENT",
                    body,
                    subject,
                    blast_id,
                    email_result.get("external_id", ""),
                )
            else:
                result["status"] = "FAILED"
                result["error"] = email_result.get("error", "Email failed")
                BlastService.log_communication(
                    customer,
                    "EMAIL" if not result.get("fallback") else "EMAIL_FALLBACK",
                    "FAILED",
                    body,
                    subject,
                    blast_id,
                    "",
                    result.get("error", ""),
                )

        return result
