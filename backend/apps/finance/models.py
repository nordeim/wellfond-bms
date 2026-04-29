"""
Finance models for Wellfond BMS.

Models:
- Transaction: Revenue, expense, and transfer records
- IntercompanyTransfer: Balanced transfers between entities (debit=credit)
- GSTReport: Quarterly GST summaries for IRAS filing
- PNLSnapshot: Monthly profit & loss snapshots
"""
import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


class TransactionType(models.TextChoices):
    """Transaction type enumeration."""
    REVENUE = "REVENUE", "Revenue"
    EXPENSE = "EXPENSE", "Expense"
    TRANSFER = "TRANSFER", "Transfer"


class TransactionCategory(models.TextChoices):
    """Transaction category enumeration."""
    SALE = "SALE", "Sale"
    VET = "VET", "Veterinary"
    MARKETING = "MARKETING", "Marketing"
    OPERATIONS = "OPERATIONS", "Operations"
    OTHER = "OTHER", "Other"


class Transaction(models.Model):
    """
    Financial transaction record.

    Attributes:
        id: UUID primary key
        type: REVENUE, EXPENSE, or TRANSFER
        amount: Transaction amount (Decimal, 12 digits, 2 decimals)
        entity: Reference to Entity
        gst_component: GST amount extracted from transaction
        date: Transaction date
        category: Classification (SALE, VET, MARKETING, OPERATIONS, OTHER)
        description: Optional transaction description
        source_agreement: Optional reference to SalesAgreement
        created_at: Timestamp when record was created
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.CASCADE,
        related_name="transactions",
        db_index=True,
    )
    gst_component = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    date = models.DateField(db_index=True)
    category = models.CharField(
        max_length=20,
        choices=TransactionCategory.choices,
        db_index=True,
    )
    description = models.TextField(blank=True, default="")
    source_agreement = models.ForeignKey(
        "sales.SalesAgreement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity", "date", "type"]),
            models.Index(fields=["entity", "category", "date"]),
            models.Index(fields=["date", "type", "category"]),
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.type}: {self.amount} ({self.entity.name})"


class IntercompanyTransfer(models.Model):
    """
    Intercompany transfer between entities.

    Constraint: Must be balanced (debit = credit).
    Creates two Transaction records automatically.

    Attributes:
        id: UUID primary key
        from_entity: Source entity
        to_entity: Destination entity
        amount: Transfer amount (must be positive)
        date: Transfer date
        description: Transfer description/reason
        created_by: User who created the transfer
        created_at: Timestamp when record was created
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.CASCADE,
        related_name="transfers_out",
        db_index=True,
    )
    to_entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.CASCADE,
        related_name="transfers_in",
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date = models.DateField(db_index=True)
    description = models.TextField(default="")
    created_by = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="intercompany_transfers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["from_entity", "date"]),
            models.Index(fields=["to_entity", "date"]),
            models.Index(fields=["date", "created_at"]),
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.from_entity.name} → {self.to_entity.name}: {self.amount}"

    def save(self, *args, **kwargs):
        """Override save to create balanced transaction records."""
        from decimal import Decimal

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            # Refresh to get entity names
            from_entity = self.from_entity
            to_entity = self.to_entity
            from_entity_name = getattr(from_entity, 'name', str(from_entity.id))[:50]
            to_entity_name = getattr(to_entity, 'name', str(to_entity.id))[:50]
            
            # Create balancing transaction records
            # From entity: EXPENSE (debit)
            Transaction.objects.create(
                type=TransactionType.EXPENSE,
                amount=self.amount,
                entity=from_entity,
                gst_component=Decimal("0.00"),
                date=self.date,
                category=TransactionCategory.OTHER,
                description=f"Intercompany transfer to {to_entity_name}: {self.description}"[:200],
            )
            # To entity: REVENUE (credit)
            Transaction.objects.create(
                type=TransactionType.REVENUE,
                amount=self.amount,
                entity=to_entity,
                gst_component=Decimal("0.00"),
                date=self.date,
                category=TransactionCategory.OTHER,
                description=f"Intercompany transfer from {from_entity_name}: {self.description}"[:200],
            )


class GSTReport(models.Model):
    """
    Quarterly GST report for IRAS filing.

    Generated deterministically from SalesAgreement GST components.
    Thomson entity: 0% GST exempt.

    Attributes:
        id: UUID primary key
        entity: Reference to Entity
        quarter: Quarter identifier (e.g., "2026-Q1")
        total_sales: Total sales amount for quarter
        total_gst: Total GST collected for quarter
        generated_at: Timestamp when report was generated
        generated_by: User who generated the report
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.CASCADE,
        related_name="gst_reports",
        db_index=True,
    )
    quarter = models.CharField(max_length=7, db_index=True)  # Format: "YYYY-QN"
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_gst = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="generated_gst_reports",
    )

    class Meta:
        unique_together = [["entity", "quarter"]]
        indexes = [
            models.Index(fields=["entity", "quarter", "generated_at"]),
        ]
        ordering = ["-quarter", "-generated_at"]

    def __str__(self) -> str:
        return f"GST {self.quarter}: {self.entity.name} = {self.total_gst}"


class PNLSnapshot(models.Model):
    """
    Monthly Profit & Loss snapshot.

    Captures P&L data at a point in time for reporting.
    Calculated from Transactions and SalesAgreements.

    Singapore Fiscal Year: April - March
    YTD calculations start from April.

    Attributes:
        id: UUID primary key
        entity: Reference to Entity
        month: First day of month
        revenue: Total revenue
        cogs: Cost of goods sold
        expenses: Operating expenses
        net: Net profit/loss (revenue - cogs - expenses)
        generated_at: Timestamp when snapshot was created
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(
        "core.Entity",
        on_delete=models.CASCADE,
        related_name="pnl_snapshots",
        db_index=True,
    )
    month = models.DateField(db_index=True)  # First day of month
    revenue = models.DecimalField(max_digits=12, decimal_places=2)
    cogs = models.DecimalField(max_digits=12, decimal_places=2)
    expenses = models.DecimalField(max_digits=12, decimal_places=2)
    net = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["entity", "month"]]
        indexes = [
            models.Index(fields=["entity", "month", "generated_at"]),
            models.Index(fields=["month", "net"]),
        ]
        ordering = ["-month"]

    def __str__(self) -> str:
        return f"P&L {self.month}: {self.entity.name} = {self.net}"
