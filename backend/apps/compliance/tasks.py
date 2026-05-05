"""Compliance Celery Tasks
==========================
Phase 6: Compliance & NParks Reporting

Celery tasks for automated compliance operations:
- Monthly NParks document generation
- Automatic submission locking
- GST ledger updates
"""

import logging
from datetime import date, timedelta
from uuid import UUID

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from django.utils import timezone

from apps.core.models import Entity

from .models import NParksSubmission, NParksStatus, GSTLedger
from .services.nparks import NParksService
from .services.gst import GSTService

logger = logging.getLogger(__name__)


@shared_task(
    queue="high",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def generate_monthly_nparks(self, entity_id: str, month_str: str):
    """
    Generate NParks documents for entity and month.
    
    Scheduled via Celery Beat on 1st of month at 9am SGT.
    Creates DRAFT submission with all 5 documents.
    
    Args:
        entity_id: Entity UUID string
        month_str: Month in YYYY-MM-DD format (first day of month)
    """
    try:
        entity = Entity.objects.get(id=entity_id)
        month = date.fromisoformat(month_str)
        
        logger.info(f"Starting monthly NParks generation for {entity.name} - {month.strftime('%Y-%m')}")
        
        # Check if submission already exists
        existing = NParksSubmission.objects.filter(
            entity=entity,
            month=month,
        ).first()
        
        if existing:
            logger.warning(f"NParks submission already exists for {entity.name} - {month.strftime('%Y-%m')}")
            return {
                "status": "skipped",
                "reason": "Submission already exists",
                "submission_id": str(existing.id),
            }
        
        # Generate documents (system user)
        from apps.core.models import User
        system_user = User.objects.filter(role="management").first()
        
        if not system_user:
            logger.error("No management user found for system generation")
            raise Exception("No management user available")
        
        documents = NParksService.generate_nparks(
            entity_id=entity.id,
            month=month,
            generated_by_id=system_user.id,
        )
        
        # Get created submission
        submission = NParksSubmission.objects.get(
            entity=entity,
            month=month,
            status=NParksStatus.DRAFT,
        )
        
        logger.info(
            f"Successfully generated NParks documents for {entity.name} - {month.strftime('%Y-%m')} "
            f"(Submission: {submission.id})"
        )
        
        return {
            "status": "success",
            "submission_id": str(submission.id),
            "entity": entity.name,
            "month": month.strftime('%Y-%m'),
            "documents_generated": len(documents),
        }
        
    except Entity.DoesNotExist:
        logger.error(f"Entity not found: {entity_id}")
        raise
        
    except Exception as exc:
        logger.error(f"NParks generation failed: {exc}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying NParks generation ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc)
        else:
            logger.error(f"Max retries exceeded for NParks generation")
            raise MaxRetriesExceededError(f"Failed to generate NParks for entity {entity_id}")


@shared_task(
    queue="high",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def lock_expired_submissions(self):
    """
    Auto-lock NParks submissions where month has passed and status is SUBMITTED.
    
    Scheduled via Celery Beat daily at midnight SGT.
    Prevents edits to past submissions.
    """
    try:
        logger.info("Starting expired NParks submission lock process")
        
        # Find submissions to lock:
        # - Status is SUBMITTED
        # - Month has ended (month < current month)
        today = timezone.now().date()
        
        # Calculate first day of current month
        current_month = today.replace(day=1)
        
        submissions = NParksSubmission.objects.filter(
            status=NParksStatus.SUBMITTED,
            month__lt=current_month,
        )
        
        locked_count = 0
        
        for submission in submissions:
            try:
                with transaction.atomic():
                    submission.status = NParksStatus.LOCKED
                    submission.locked_at = timezone.now()
                    submission.save(update_fields=["status", "locked_at"])
                    
                    logger.info(f"Auto-locked NParks submission {submission.id}")
                    locked_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to lock submission {submission.id}: {e}")
                continue
        
        logger.info(f"Locked {locked_count} expired NParks submissions")
        
        return {
            "status": "success",
            "locked_count": locked_count,
            "checked_count": submissions.count(),
        }
        
    except Exception as exc:
        logger.error(f"Lock expired submissions failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        else:
            raise MaxRetriesExceededError("Failed to lock expired submissions")


@shared_task(
    queue="default",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def create_gst_ledger_entry(self, agreement_id: str):
    """
    Create GST ledger entry for completed sales agreement.
    
    Called when agreement is marked as COMPLETED.
    
    Args:
        agreement_id: SalesAgreement UUID string
    """
    try:
        from apps.sales.models import SalesAgreement, AgreementStatus
        
        agreement = SalesAgreement.objects.get(id=agreement_id)
        
        # Only create entry for completed agreements
        if agreement.status != AgreementStatus.COMPLETED:
            logger.warning(f"Agreement {agreement_id} is not completed, skipping GST ledger")
            return {
                "status": "skipped",
                "reason": "Agreement not completed",
            }
        
        entry = GSTService.create_ledger_entry(agreement)
        
        if entry:
            logger.info(f"Created GST ledger entry {entry.id} for agreement {agreement_id}")
            return {
                "status": "success",
                "ledger_id": str(entry.id),
                "agreement_id": agreement_id,
            }
        else:
            logger.warning(f"No GST ledger entry created for agreement {agreement_id}")
            return {
                "status": "skipped",
                "reason": "Entry not created (see logs)",
            }
            
    except SalesAgreement.DoesNotExist:
        logger.error(f"SalesAgreement not found: {agreement_id}")
        raise
        
    except Exception as exc:
        logger.error(f"GST ledger creation failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        else:
            raise MaxRetriesExceededError(f"Failed to create GST ledger for agreement {agreement_id}")


@shared_task(queue="low")
def cleanup_old_nparks_drafts(days: int = 90):
    """
    Clean up old DRAFT NParks submissions.
    
    Removes draft submissions older than specified days.
    Should be run monthly.
    
    Args:
        days: Age in days before cleanup (default 90)
    """
    try:
        cutoff = timezone.now() - timedelta(days=days)
        
        old_drafts = NParksSubmission.objects.filter(
            status=NParksStatus.DRAFT,
            created_at__lt=cutoff,
        )
        
        count = old_drafts.count()
        old_drafts.delete()
        
        logger.info(f"Cleaned up {count} old NParks draft submissions")
        
        return {
            "status": "success",
            "deleted_count": count,
            "cutoff_days": days,
        }
        
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        return {
            "status": "error",
            "error": str(exc),
        }


@shared_task(queue="default")
def validate_all_entities_for_month(month_str: str = None):
    """
    Validate NParks requirements for all entities for a given month.
    
    Generates warning reports for management review.
    
    Args:
        month_str: Month in YYYY-MM format (default: previous month)
    """
    try:
        if month_str:
            year, month = month_str.split("-")
            month_date = date(int(year), int(month), 1)
        else:
            # Default to previous month
            today = timezone.now().date()
            if today.month == 1:
                month_date = date(today.year - 1, 12, 1)
            else:
                month_date = date(today.year, today.month - 1, 1)
        
        entities = Entity.objects.filter(is_active=True)
        
        reports = []
        
        for entity in entities:
            warnings = NParksService.validate_nparks(
                entity_id=entity.id,
                month=month_date,
            )
            
            if warnings:
                reports.append({
                    "entity": entity.name,
                    "warnings": warnings,
                })
                logger.warning(f"NParks validation warnings for {entity.name}: {warnings}")
        
        return {
            "status": "success",
            "month": month_date.strftime("%Y-%m"),
            "entities_checked": entities.count(),
            "entities_with_warnings": len(reports),
            "reports": reports,
        }
        
    except Exception as exc:
        logger.error(f"Validation failed: {exc}")
        return {
            "status": "error",
            "error": str(exc),
        }
