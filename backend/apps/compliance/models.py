"""Compliance & NParks Reporting Models
========================================
Phase 6: Compliance & NParks Reporting

Models:
- NParksSubmission: Monthly NParks reporting submissions
- GSTLedger: GST transaction tracking
- PDPAConsentLog: Immutable PDPA consent audit trail
"""

from decimal import Decimal
from uuid import uuid4

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class NParksStatus(models.TextChoices):
    """NParks submission status."""
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    LOCKED = "LOCKED", "Locked"


class PDPAAction(models.TextChoices):
    """PDPA consent actions."""
    OPT_IN = "OPT_IN", "Opt In"
    OPT_OUT = "OPT_OUT", "Opt Out"


class NParksSubmission(models.Model):
    """
    NParks monthly submission tracking.

    Tracks the generation, submission, and locking of NParks reports.
    Once LOCKED, the submission is immutable.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Entity (multi-tenancy)
    entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.PROTECT,
        related_name="nparks_submissions",
    )

    # Reporting period
    month = models.DateField(
        help_text="First day of the reporting month",
    )

    # Status
    status = models.CharField(
        max_length=15,
        choices=NParksStatus.choices,
        default=NParksStatus.DRAFT,
        db_index=True,
    )

    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    # Audit
    generated_by = models.ForeignKey(
        "core.User",
        on_delete=models.PROTECT,
        related_name="generated_nparks_submissions",
    )

    # File storage (optional - can store in S3/R2)
    mating_sheet_url = models.URLField(blank=True)
    puppy_movement_url = models.URLField(blank=True)
    vet_treatments_url = models.URLField(blank=True)
    puppies_bred_url = models.URLField(blank=True)
    dog_movement_url = models.URLField(blank=True)

    class Meta:
        db_table = "compliance_nparks_submissions"
        ordering = ["-month"]
        unique_together = ["entity", "month"]
        indexes = [
            models.Index(fields=["entity", "status", "month"]),
            models.Index(fields=["status", "generated_at"]),
        ]

    def __str__(self) -> str:
        return f"NParks {self.entity.name} - {self.month.strftime('%Y-%m')} ({self.status})"

    def is_locked(self) -> bool:
        """Check if submission is locked."""
        return self.status == NParksStatus.LOCKED


class GSTLedger(models.Model):
    """
    GST transaction ledger.

    Records GST components for each sales agreement.
    Immutable once created.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Entity (multi-tenancy)
    entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.PROTECT,
        related_name="gst_ledger_entries",
    )

    # Reporting period (quarter)
    period = models.CharField(
        max_length=7,  # Format: "2026-Q1"
        help_text="Quarter format: YYYY-Q#",
        db_index=True,
    )

    # Source transaction
    source_agreement = models.ForeignKey(
        "sales.SalesAgreement",
        on_delete=models.PROTECT,
        related_name="gst_ledger_entries",
    )

    # GST data
    total_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    gst_component = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_gst_ledger"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "period"]),
            models.Index(fields=["source_agreement"]),
        ]

    def __str__(self) -> str:
        return f"GST {self.period} - {self.entity.name} - ${self.gst_component}"


class PDPAConsentLog(models.Model):
    """
    Immutable PDPA consent audit trail.

    Records all consent changes for compliance.
    No UPDATE or DELETE allowed (enforced at DB level).
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Customer (UUID reference - will become ForeignKey when customers app exists)
    customer_id = models.UUIDField(
        help_text="Customer UUID reference",
        db_index=True,
    )

    # Consent change
    action = models.CharField(
        max_length=10,
        choices=PDPAAction.choices,
    )
    previous_state = models.BooleanField()
    new_state = models.BooleanField()

    # Audit
    actor = models.ForeignKey(
        "core.User",
        on_delete=models.PROTECT,
        related_name="pdpa_consent_changes",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_pdpa_consent_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer_id", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"PDPA {self.action} - {self.customer_id} at {self.created_at}"

    def save(self, *args, **kwargs):
        """Prevent updates - append-only."""
        if not self._state.adding:
            raise ValueError("PDPAConsentLog is immutable - cannot update")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion - append-only."""
        raise ValueError("PDPAConsentLog is immutable - cannot delete")
