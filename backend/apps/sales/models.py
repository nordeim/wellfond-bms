"""Sales Agreement Models — Phase 5: Sales & AVS Tracking."""

from decimal import Decimal
from uuid import uuid4

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class AgreementType(models.TextChoices):
    """Types of sales agreements."""
    B2C = "B2C", "Business to Consumer"
    B2B = "B2B", "Business to Business"
    REHOME = "REHOME", "Rehoming"


class AgreementStatus(models.TextChoices):
    """Status of sales agreement."""
    DRAFT = "DRAFT", "Draft"
    SIGNED = "SIGNED", "Signed"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class HousingType(models.TextChoices):
    """Buyer housing types for HDB compliance."""
    HDB = "HDB", "HDB"
    CONDO = "CONDO", "Condominium"
    LANDED = "LANDED", "Landed Property"
    OTHER = "OTHER", "Other"


class PaymentMethod(models.TextChoices):
    """Payment methods for agreements."""
    CASH = "CASH", "Cash"
    PAYNOW = "PAYNOW", "PayNow"
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    CREDIT_CARD = "CREDIT_CARD", "Credit Card"
    INSTALLMENT = "INSTALLMENT", "Installment"


class AVSStatus(models.TextChoices):
    """AVS transfer status."""
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    COMPLETED = "COMPLETED", "Completed"
    ESCALATED = "ESCALATED", "Escalated"


class SignerType(models.TextChoices):
    """Type of signer."""
    SELLER = "SELLER", "Seller"
    BUYER = "BUYER", "Buyer"


class SignatureMethod(models.TextChoices):
    """Signature capture method."""
    IN_PERSON = "IN_PERSON", "In Person"
    REMOTE = "REMOTE", "Remote"
    PAPER = "PAPER", "Paper"


class SalesAgreement(models.Model):
    """
    Sales agreement for dog sales (B2C, B2B, or Rehoming).

    Tracks buyer information, pricing, GST, signatures, and AVS status.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Agreement type and status
    type = models.CharField(
        max_length=10,
        choices=AgreementType.choices,
        default=AgreementType.B2C,
    )
    status = models.CharField(
        max_length=15,
        choices=AgreementStatus.choices,
        default=AgreementStatus.DRAFT,
        db_index=True,
    )

    # Entity (multi-tenancy)
    entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.PROTECT,
        related_name="sales_agreements",
    )

    # Buyer information
    buyer_name = models.CharField(max_length=200)
    buyer_nric = models.CharField(max_length=20, blank=True, verbose_name="NRIC/FIN")
    buyer_mobile = models.CharField(max_length=15)
    buyer_email = models.EmailField()
    buyer_address = models.TextField()
    buyer_housing_type = models.CharField(
        max_length=10,
        choices=HousingType.choices,
        default=HousingType.OTHER,
    )

    # PDPA consent
    pdpa_consent = models.BooleanField(default=False)

    # Pricing
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    gst_component = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )

    # Special conditions
    special_conditions = models.TextField(blank=True)

    # PDF and integrity
    pdf_hash = models.CharField(max_length=64, blank=True)  # SHA-256
    pdf_url = models.URLField(blank=True)

    # Signatures
    signed_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_by = models.ForeignKey(
        "core.User",
        on_delete=models.PROTECT,
        related_name="created_agreements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_agreements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "status", "created_at"]),
            models.Index(fields=["type", "status"]),
            models.Index(fields=["buyer_mobile"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} - {self.buyer_name} - {self.total_amount}"


class AgreementLineItem(models.Model):
    """
    Line item for dogs included in a sales agreement.

    Tracks individual dog pricing and GST per item.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    agreement = models.ForeignKey(
        SalesAgreement,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    dog = models.ForeignKey(
        "operations.Dog",
        on_delete=models.PROTECT,
        related_name="sales_line_items",
    )

    # Pricing per item
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    gst_component = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_line_items"
        unique_together = ["agreement", "dog"]
        indexes = [
            models.Index(fields=["agreement", "dog"]),
        ]

    def __str__(self) -> str:
        return f"{self.dog.name} - ${self.price}"


class AVSTransfer(models.Model):
    """
    AVS (Animal & Veterinary Service) transfer tracking.

    Tracks the transfer of ownership notification to AVS.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    agreement = models.ForeignKey(
        SalesAgreement,
        on_delete=models.CASCADE,
        related_name="avs_transfers",
    )
    dog = models.ForeignKey(
        "operations.Dog",
        on_delete=models.PROTECT,
        related_name="avs_transfers",
    )

    # Buyer contact
    buyer_mobile = models.CharField(max_length=15)

    # Unique token for transfer link
    token = models.CharField(max_length=36, unique=True, db_index=True)

    # Status tracking
    status = models.CharField(
        max_length=15,
        choices=AVSStatus.choices,
        default=AVSStatus.PENDING,
        db_index=True,
    )

    # Reminder tracking
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_avs_transfers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agreement", "status"]),
            models.Index(fields=["dog", "status"]),
            models.Index(fields=["token"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"AVS {self.dog.name} - {self.status}"


class Signature(models.Model):
    """
    Electronic or physical signature capture for agreements.

    Stores signature coordinates, method, and audit info.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    agreement = models.ForeignKey(
        SalesAgreement,
        on_delete=models.CASCADE,
        related_name="signatures",
    )

    signer_type = models.CharField(
        max_length=10,
        choices=SignerType.choices,
    )
    method = models.CharField(
        max_length=15,
        choices=SignatureMethod.choices,
    )

    # Signature data (coordinates for digital)
    coordinates = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {x, y, timestamp} for digital signatures",
    )

    # Audit
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Image (for remote/paper signatures)
    image_url = models.URLField(blank=True)

    class Meta:
        db_table = "sales_signatures"
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["agreement", "signer_type"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.signer_type} signature - {self.method}"


class TCTemplate(models.Model):
    """
    Terms & Conditions template for agreements.

    Versioned T&C content by agreement type.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    type = models.CharField(
        max_length=10,
        choices=AgreementType.choices,
        unique=True,
    )
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)

    # Audit
    updated_by = models.ForeignKey(
        "core.User",
        on_delete=models.PROTECT,
        related_name="updated_tc_templates",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_tc_templates"
        ordering = ["-version"]
        indexes = [
            models.Index(fields=["type", "version"]),
        ]

    def __str__(self) -> str:
        return f"T&C {self.type} v{self.version}"
