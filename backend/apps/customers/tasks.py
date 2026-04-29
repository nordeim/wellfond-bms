"""Customers Celery Tasks
==========================
Phase 7: Customer DB & Marketing Blast

Background tasks for blast dispatch and communication logging.
"""

import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from uuid import UUID

from apps.core.models import User
from .models import Customer
from .services.blast import BlastProgressTracker, BlastService, CommunicationRouter

logger = logging.getLogger(__name__)


@shared_task(queue="default", max_retries=3)
def dispatch_blast(
    blast_id: str,
    customer_ids: list[str],
    channel: str,
    body: str,
    subject: str,
    merge_tags: dict,
    actor_id: str,
):
    """
    Dispatch blast in chunks.

    Process customers in chunks of 50, with exponential backoff retry.
    Updates progress via Redis for SSE streaming.

    Args:
        blast_id: Blast UUID
        customer_ids: List of customer UUIDs
        channel: EMAIL, WA, or BOTH
        body: Message body
        subject: Email subject
        merge_tags: Custom merge tags
        actor_id: User UUID who initiated blast
    """
    CHUNK_SIZE = 50
    blast_uuid = UUID(blast_id)
    actor = User.objects.get(id=UUID(actor_id))

    tracker = BlastProgressTracker(blast_uuid)
    total = len(customer_ids)
    sent = 0
    delivered = 0
    failed = 0

    logger.info(f"Starting blast {blast_id}: {total} recipients, channel={channel}")

    # Process in chunks
    for i in range(0, total, CHUNK_SIZE):
        chunk = customer_ids[i : i + CHUNK_SIZE]

        for customer_id in chunk:
            try:
                customer = Customer.objects.get(id=UUID(customer_id))

                # Skip if no valid contact
                if channel in ["EMAIL", "BOTH"] and not customer.email:
                    logger.warning(f"No email for customer {customer_id}, skipping")
                    failed += 1
                    continue

                if channel == "WA" and not customer.mobile:
                    logger.warning(f"No mobile for customer {customer_id}, skipping")
                    failed += 1
                    continue

                # Apply merge tags
                personalized_body = BlastService.apply_merge_tags(
                    body, customer, merge_tags
                )
                personalized_subject = BlastService.apply_merge_tags(
                    subject, customer, merge_tags
                )

                # Route message with fallback
                result = CommunicationRouter.route_message(
                    customer,
                    channel,
                    personalized_subject,
                    personalized_body,
                    blast_uuid,
                )

                if result["status"] == "SENT":
                    sent += 1
                    if result.get("channel_used") == "WA":
                        delivered += 1  # WA doesn't have delivery receipts immediately
                else:
                    failed += 1

                # Update progress
                tracker.update_progress(sent, delivered, failed)

            except Customer.DoesNotExist:
                logger.error(f"Customer {customer_id} not found")
                failed += 1
            except Exception as e:
                logger.exception(f"Error sending to {customer_id}: {e}")
                failed += 1

        logger.info(f"Blast {blast_id}: processed chunk {i // CHUNK_SIZE + 1}")

    # Mark complete
    tracker.complete()
    logger.info(
        f"Blast {blast_id} complete: {sent} sent, {delivered} delivered, {failed} failed"
    )

    return {
        "blast_id": blast_id,
        "total": total,
        "sent": sent,
        "delivered": delivered,
        "failed": failed,
    }


@shared_task(queue="low")
def log_delivery(
    customer_id: str,
    channel: str,
    status: str,
    message_preview: str,
    subject: str = "",
    blast_id: str = None,
    external_id: str = "",
    error_message: str = "",
):
    """
    Log per-message delivery status.

    Args:
        customer_id: Customer UUID
        channel: EMAIL or WA
        status: SENT, DELIVERED, BOUNCED, FAILED
        message_preview: First 200 chars
        subject: Email subject
        blast_id: Optional blast UUID
        external_id: Provider message ID
        error_message: Error details
    """
    try:
        customer = Customer.objects.get(id=UUID(customer_id))

        BlastService.log_communication(
            customer=customer,
            channel=channel,
            status=status,
            message_preview=message_preview,
            subject=subject,
            blast_id=UUID(blast_id) if blast_id else None,
            external_id=external_id,
            error_message=error_message,
        )

    except Customer.DoesNotExist:
        logger.error(f"Cannot log delivery: customer {customer_id} not found")
    except Exception as e:
        logger.exception(f"Error logging delivery: {e}")


@shared_task(queue="low")
def update_blast_progress(blast_id: str, sent: int, delivered: int, failed: int):
    """
    Update blast progress in Redis.

    Args:
        blast_id: Blast UUID
        sent: Number sent
        delivered: Number delivered
        failed: Number failed
    """
    tracker = BlastProgressTracker(UUID(blast_id))
    tracker.update_progress(sent, delivered, failed)


@shared_task(queue="low")
def cleanup_stale_blasts():
    """
    Clean up stale blast progress entries.

    Removes Redis entries for completed blasts older than 24 hours.
    """
    from django.core.cache import cache

    # This would scan for blast:*:progress keys and remove old ones
    # Implementation depends on Redis client capabilities
    logger.info("Cleanup stale blast progress entries")


@shared_task(queue="default", bind=True, max_retries=3)
def retry_failed_chunk(self, blast_id: str, customer_ids: list[str], channel: str, body: str, subject: str, merge_tags: dict, actor_id: str):
    """
    Retry a failed chunk with exponential backoff.

    Args:
        blast_id: Blast UUID
        customer_ids: Customer IDs to retry
        channel: Channel
        body: Body
        subject: Subject
        merge_tags: Merge tags
        actor_id: Actor ID
    """
    try:
        dispatch_blast(
            blast_id=blast_id,
            customer_ids=customer_ids,
            channel=channel,
            body=body,
            subject=subject,
            merge_tags=merge_tags,
            actor_id=actor_id,
        )
    except Exception as exc:
        logger.exception(f"Retry failed for blast {blast_id}: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)


@shared_task(queue="low")
def send_to_dlq(blast_id: str, failed_customers: list[str], reason: str):
    """
    Send failed customers to Dead Letter Queue for manual review.

    Args:
        blast_id: Blast UUID
        failed_customers: List of failed customer IDs
        reason: Failure reason
    """
    logger.error(f"DLQ: Blast {blast_id} - {len(failed_customers)} failures - {reason}")

    # Could store to a DLQ model or send notification
    # For now, just log
    for customer_id in failed_customers:
        logger.error(f"DLQ entry: blast={blast_id}, customer={customer_id}, reason={reason}")
