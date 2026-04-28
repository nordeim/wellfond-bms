"""GST Service
=============
Phase 6: Compliance & NParks Reporting

Deterministic GST calculation and reporting.
Zero AI - pure Python/SQL logic.

GST Formula: price * 9 / 109, ROUND_HALF_UP
Thomson entity: 0% GST exempt
"""

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from uuid import UUID

from apps.core.models import Entity
from apps.sales.models import SalesAgreement

from ..models import GSTLedger
from ..schemas import GSTCalculationResponse, GSTCalculationRequest, GSTSummary, GSTLedgerEntry

logger = logging.getLogger(__name__)


class GSTService:
    """Service for GST calculation and reporting."""

    # Default GST rate (9%)
    DEFAULT_GST_RATE = Decimal("0.09")

    @staticmethod
    def extract_gst(price: Decimal, entity: Entity) -> Decimal:
        """
        Extract GST component from price using Singapore GST formula.

        Formula: price * 9 / 109, rounded to 2 decimals (HALF_UP)

        Thomson entity has 0% GST (exempt).

        Args:
            price: Total price including GST
            entity: Entity for GST determination

        Returns:
            GST component amount
        """
        # Thomson entity is GST exempt
        if entity.code.upper() == "THOMSON":
            return Decimal("0.00")

        # Get entity's GST rate (default 9%)
        gst_rate = Decimal(str(entity.gst_rate))

        # GST = price * rate / (1 + rate)
        # For 9%: price * 9 / 109
        divisor = Decimal("1") + gst_rate
        gst = price * gst_rate / divisor

        return gst.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_gst(price: Decimal, entity: Entity) -> tuple[Decimal, Decimal]:
        """
        Calculate price without GST and GST component.

        Args:
            price: Total price including GST
            entity: Entity for GST determination

        Returns:
            Tuple of (price_excl_gst, gst_component)
        """
        gst = GSTService.extract_gst(price, entity)
        price_excl = price - gst

        return price_excl, gst

    @staticmethod
    def calculate_gst_from_request(request: GSTCalculationRequest) -> GSTCalculationResponse:
        """
        Calculate GST from API request.

        Args:
            request: GST calculation request

        Returns:
            GST calculation response
        """
        entity = Entity.objects.get(id=request.entity_id)

        subtotal, gst_component = GSTService.calculate_gst(request.price, entity)

        return GSTCalculationResponse(
            price=request.price,
            gst_rate=entity.gst_rate,
            gst_component=gst_component,
            subtotal=subtotal,
            total=request.price,
        )

    @staticmethod
    def get_quarter_from_date(d: date) -> str:
        """
        Get quarter string from date.

        Args:
            d: Date

        Returns:
            Quarter string (e.g., "2026-Q1")
        """
        quarter = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{quarter}"

    @staticmethod
    def calc_gst_summary(entity: Entity, quarter: str) -> GSTSummary:
        """
        Calculate GST summary for entity and quarter.

        Args:
            entity: Entity
            quarter: Quarter string (e.g., "2026-Q1")

        Returns:
            GST summary
        """
        # Parse quarter
        year, q = quarter.split("-")
        year = int(year)
        quarter_num = int(q.replace("Q", ""))

        # Calculate date range
        start_month = (quarter_num - 1) * 3 + 1
        from apps.sales.models import AgreementStatus

        # Get all completed agreements in quarter
        from datetime import datetime, timedelta

        # Create date range for quarter
        if start_month == 1:
            start_date = date(year, 1, 1)
            end_date = date(year, 3, 31)
        elif start_month == 4:
            start_date = date(year, 4, 1)
            end_date = date(year, 6, 30)
        elif start_month == 7:
            start_date = date(year, 7, 1)
            end_date = date(year, 9, 30)
        else:  # start_month == 10
            start_date = date(year, 10, 1)
            end_date = date(year, 12, 31)

        agreements = SalesAgreement.objects.filter(
            entity=entity,
            status=AgreementStatus.COMPLETED,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        )

        total_sales = sum(a.total_amount for a in agreements)
        total_gst = sum(a.gst_component for a in agreements)
        transactions_count = agreements.count()

        return GSTSummary(
            entity_id=entity.id,
            entity_name=entity.name,
            quarter=quarter,
            total_sales=total_sales,
            total_gst=total_gst,
            transactions_count=transactions_count,
        )

    @staticmethod
    def create_ledger_entry(agreement: SalesAgreement) -> Optional[GSTLedger]:
        """
        Create GST ledger entry for completed agreement.

        Args:
            agreement: SalesAgreement

        Returns:
            Created GSTLedger entry or None if not completed
        """
        from apps.sales.models import AgreementStatus

        if agreement.status != AgreementStatus.COMPLETED:
            return None

        # Get quarter from completion date
        if not agreement.completed_at:
            return None

        quarter = GSTService.get_quarter_from_date(agreement.completed_at.date())

        # Create or update ledger entry
        entry, created = GSTLedger.objects.update_or_create(
            entity=agreement.entity,
            source_agreement=agreement,
            defaults={
                "period": quarter,
                "total_sales": agreement.total_amount,
                "gst_component": agreement.gst_component,
            },
        )

        if created:
            logger.info(f"Created GST ledger entry for agreement {agreement.id}")

        return entry

    @staticmethod
    def get_ledger_entries(entity: Entity, quarter: str) -> list[GSTLedgerEntry]:
        """
        Get GST ledger entries for entity and quarter.

        Args:
            entity: Entity
            quarter: Quarter string (e.g., "2026-Q1")

        Returns:
            List of ledger entries as schemas
        """
        entries = GSTLedger.objects.filter(
            entity=entity,
            period=quarter,
        ).select_related("source_agreement")

        return [
            GSTLedgerEntry(
                id=e.id,
                agreement_id=e.source_agreement_id,
                agreement_number=str(e.source_agreement.id)[:8],  # Or use actual agreement number
                buyer_name=e.source_agreement.buyer_name,
                total_sales=e.total_sales,
                gst_component=e.gst_component,
                created_at=e.created_at,
            )
            for e in entries
        ]

    @staticmethod
    def validate_gst_calculation(price: Decimal, expected_gst: Decimal) -> bool:
        """
        Validate GST calculation against expected value.

        Args:
            price: Total price
            expected_gst: Expected GST component

        Returns:
            True if calculation matches
        """
        # Use default GST rate for validation
        expected = (price * GSTService.DEFAULT_GST_RATE / (Decimal("1") + GSTService.DEFAULT_GST_RATE))
        expected = expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return expected == expected_gst.quantize(Decimal("0.01"))
