"""Customer Models
=================
Phase 7: Customer DB & Marketing Blast

Models:
- Customer: Customer records with PDPA consent tracking
- CommunicationLog: Immutable communication history
- Segment: Marketing segments with JSON filters
"""

from uuid import uuid4

from django.db import models

from apps.core.models import Entity, User


class HousingType(models.TextChoices):
    """Housing type choices."""

    HDB = "HDB", "HDB"
    CONDO = "CONDO", "Condominium"
    LANDED = "LANDED", "Landed Property"
    OTHER = "OTHER", "Other"


class CommunicationChannel(models.TextChoices):
    """Communication channel choices."""

    EMAIL = "EMAIL", "Email"
    WA = "WA", "WhatsApp"


class CommunicationStatus(models.TextChoices):
    """Communication status choices."""

    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    DELIVERED = "DELIVERED", "Delivered"
    BOUNCED = "BOUNCED", "Bounced"
    FAILED = "FAILED", "Failed"


class Customer(models.Model):
    """
    Customer record with PDPA consent tracking.

    Tracks buyer information from sales agreements and manual entry.
    PDPA consent is mandatory for marketing communications.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Personal Information
    name = models.CharField(max_length=255)
    nric = models.CharField(max_length=20, blank=True, db_index=True)
    mobile = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Housing Information
    housing_type = models.CharField(
        max_length=10,
        choices=HousingType.choices,
        blank=True,
    )

    # PDPA Consent (critical for marketing compliance)
    pdpa_consent = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Customer has opted in to marketing communications",
    )
    pdpa_consent_date = models.DateTimeField(null=True, blank=True)

    # Multi-tenancy
    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="customers",
    )

    # Notes
    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_customers",
    )

    class Meta:
        db_table = "customers_customer"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "pdpa_consent"]),
            models.Index(fields=["housing_type"]),
            models.Index(fields=["name"]),
        ]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self) -> str:
        return f"{self.name} ({self.mobile})"

    def can_receive_marketing(self) -> bool:
        """Check if customer can receive marketing communications."""
        return self.pdpa_consent


class CommunicationLog(models.Model):
    """
    Immutable communication history.

    Records all sent messages for compliance and audit.
    Append-only - no updates or deletes allowed.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Customer
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="communication_logs",
    )

    # Campaign reference
    campaign_id = models.CharField(max_length=100, blank=True, db_index=True)
    blast_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Communication details
    channel = models.CharField(
        max_length=10,
        choices=CommunicationChannel.choices,
    )
    status = models.CharField(
        max_length=15,
        choices=CommunicationStatus.choices,
        default=CommunicationStatus.PENDING,
    )

    # Message content (truncated for preview)
    subject = models.CharField(max_length=255, blank=True)
    message_preview = models.TextField(
        max_length=200,
        help_text="First 200 characters of message",
    )

    # Bounce/failure details
    error_message = models.TextField(blank=True)
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Resend message ID or WA message ID",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Audit
    sent_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_communications",
    )

    class Meta:
        db_table = "customers_communication_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["campaign_id"]),
            models.Index(fields=["blast_id"]),
            models.Index(fields=["channel", "status"]),
        ]
        verbose_name = "Communication Log"
        verbose_name_plural = "Communication Logs"

    def __str__(self) -> str:
        return f"{self.channel} to {self.customer.name} - {self.status}"

    def save(self, *args, **kwargs):
        """Prevent updates - append-only."""
        if not self._state.adding:
            raise ValueError("CommunicationLog is immutable - cannot update")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion - append-only."""
        raise ValueError("CommunicationLog is immutable - cannot delete")


class Segment(models.Model):
    """
    Marketing segment with JSON filters.

    Allows creating reusable customer segments for targeted blasts.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Segment details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Filters stored as JSON
    filters_json = models.JSONField(
        default=dict,
        help_text="JSON filters: breed, entity, pdpa, date_range, housing_type",
    )

    # Count cache
    customer_count = models.PositiveIntegerField(
        default=0,
        help_text="Cached count of matching customers",
    )
    count_updated_at = models.DateTimeField(null=True, blank=True)

    # Multi-tenancy
    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="segments",
        null=True,
        blank=True,
        help_text="NULL = all entities (management only)",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_segments",
    )

    class Meta:
        db_table = "customers_segment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "created_at"]),
        ]
        verbose_name = "Segment"
        verbose_name_plural = "Segments"

    def __str__(self) -> str:
        return self.name

    def invalidate_cache(self):
        """Invalidate cached count."""
        self.customer_count = 0
        self.count_updated_at = None
        self.save(update_fields=["customer_count", "count_updated_at"])
