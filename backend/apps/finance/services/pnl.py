"""
Profit & Loss calculation service.

Singapore fiscal year: April - March
YTD calculations start from April.

Formula:
  Net = Revenue - COGS - Expenses

Categories:
  - Revenue: SalesAgreement.total_amount for entity+month
  - COGS: Transaction where type=EXPENSE, category=SALE
  - Expenses: Transaction where type=EXPENSE, category≠SALE

Intercompany Elimination:
  - Transfers between entities net to zero in consolidated view
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from django.db.models import Sum, Q
from django.db import connection

if TYPE_CHECKING:
    from ..models import Transaction


# Singapore fiscal year starts in April
SG_FISCAL_START_MONTH = 4


@dataclass(frozen=True)
class PNLResult:
    """Profit & Loss calculation result."""
    entity_id: UUID
    month: date
    revenue: Decimal
    cogs: Decimal
    expenses: Decimal
    net: Decimal
    ytd_revenue: Decimal
    ytd_net: Decimal
    by_category: dict[str, Decimal]


def calc_pnl(entity_id: UUID, month: date) -> PNLResult:
    """
    Calculate P&L for entity and month.

    Args:
        entity_id: Entity UUID
        month: First day of month to calculate

    Returns:
        PNLResult with all calculations

    Example:
        >>> from datetime import date
        >>> result = calc_pnl(uuid, date(2026, 4, 1))
        >>> result.net == result.revenue - result.cogs - result.expenses
        True
    """
    from ..models import Transaction, TransactionType, TransactionCategory
    from apps.sales.models import SalesAgreement, AgreementStatus

    # Revenue: Sum of SalesAgreement.total_amount for entity+month
    revenue_data = SalesAgreement.objects.filter(
        entity_id=entity_id,
        status=AgreementStatus.COMPLETED,
        completed_at__year=month.year,
        completed_at__month=month.month,
    ).aggregate(
        total=Sum("total_amount"),
    )
    revenue = revenue_data["total"] or Decimal("0.00")

    # COGS: Expenses categorized as SALE
    cogs_data = Transaction.objects.filter(
        entity_id=entity_id,
        type=TransactionType.EXPENSE,
        category=TransactionCategory.SALE,
        date__year=month.year,
        date__month=month.month,
    ).aggregate(total=Sum("amount"))
    cogs = cogs_data["total"] or Decimal("0.00")

    # Other expenses: All expenses except SALE
    expenses_data = Transaction.objects.filter(
        entity_id=entity_id,
        type=TransactionType.EXPENSE,
        date__year=month.year,
        date__month=month.month,
    ).exclude(
        category=TransactionCategory.SALE,
    ).aggregate(total=Sum("amount"))
    expenses = expenses_data["total"] or Decimal("0.00")

    # Net profit
    net = revenue - cogs - expenses

    # Category breakdown (all expense categories)
    category_data = Transaction.objects.filter(
        entity_id=entity_id,
        type=TransactionType.EXPENSE,
        date__year=month.year,
        date__month=month.month,
    ).values("category").annotate(
        total=Sum("amount"),
    )

    by_category: dict[str, Decimal] = {}
    for item in category_data:
        by_category[item["category"]] = item["total"] or Decimal("0.00")

    # YTD calculations (from April to current month)
    ytd_revenue, ytd_net = calc_ytd(entity_id, month)

    return PNLResult(
        entity_id=entity_id,
        month=month,
        revenue=revenue,
        cogs=cogs,
        expenses=expenses,
        net=net,
        ytd_revenue=ytd_revenue,
        ytd_net=ytd_net,
        by_category=by_category,
    )


def calc_ytd(entity_id: UUID, month: date) -> tuple[Decimal, Decimal]:
    """
    Calculate YTD revenue and net from April (Singapore fiscal year).

    Args:
        entity_id: Entity UUID
        month: Current month (first day)

    Returns:
        Tuple of (ytd_revenue, ytd_net)

    Note:
        Singapore fiscal year runs April - March.
        If current month is before April, calculate from previous April.
    """
    from ..models import Transaction, TransactionType, TransactionCategory
    from apps.sales.models import SalesAgreement, AgreementStatus

    # Determine fiscal year start
    if month.month >= SG_FISCAL_START_MONTH:
        # Current fiscal year: April of current year
        fiscal_start = date(month.year, SG_FISCAL_START_MONTH, 1)
    else:
        # Previous fiscal year: April of previous year
        fiscal_start = date(month.year - 1, SG_FISCAL_START_MONTH, 1)

    # YTD Revenue
    revenue_data = SalesAgreement.objects.filter(
        entity_id=entity_id,
        status=AgreementStatus.COMPLETED,
        completed_at__date__gte=fiscal_start,
        completed_at__date__lt=month.replace(day=1),
    ).aggregate(total=Sum("total_amount"))
    ytd_revenue = revenue_data["total"] or Decimal("0.00")

    # YTD COGS
    cogs_data = Transaction.objects.filter(
        entity_id=entity_id,
        type=TransactionType.EXPENSE,
        category=TransactionCategory.SALE,
        date__gte=fiscal_start,
        date__lt=month,
    ).aggregate(total=Sum("amount"))
    ytd_cogs = cogs_data["total"] or Decimal("0.00")

    # YTD Other Expenses
    expenses_data = Transaction.objects.filter(
        entity_id=entity_id,
        type=TransactionType.EXPENSE,
        date__gte=fiscal_start,
        date__lt=month,
    ).exclude(
        category=TransactionCategory.SALE,
    ).aggregate(total=Sum("amount"))
    ytd_expenses = expenses_data["total"] or Decimal("0.00")

    ytd_net = ytd_revenue - ytd_cogs - ytd_expenses

    return ytd_revenue, ytd_net


def calc_intercompany_elimination(
    from_entity_id: UUID,
    to_entity_id: UUID,
    month: date,
) -> Decimal:
    """
    Calculate intercompany elimination amount.

    Args:
        from_entity_id: Source entity
        to_entity_id: Destination entity
        month: Month to calculate

    Returns:
        Net amount to eliminate (should net to zero)
    """
    from ..models import IntercompanyTransfer

    # Transfers in this direction
    outward = IntercompanyTransfer.objects.filter(
        from_entity_id=from_entity_id,
        to_entity_id=to_entity_id,
        date__year=month.year,
        date__month=month.month,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Transfers in reverse direction
    inward = IntercompanyTransfer.objects.filter(
        from_entity_id=to_entity_id,
        to_entity_id=from_entity_id,
        date__year=month.year,
        date__month=month.month,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Net should be zero if balanced
    return outward - inward


def get_pnl_consolidated(entity_ids: list[UUID], month: date) -> PNLResult:
    """
    Calculate consolidated P&L across multiple entities.
    
    Args:
        entity_ids: List of entity UUIDs
        month: Month to calculate
        
    Returns:
        PNLResult with consolidated figures
    """
    total_revenue = Decimal("0.00")
    total_cogs = Decimal("0.00")
    total_expenses = Decimal("0.00")
    
    for entity_id in entity_ids:
        result = calc_pnl(entity_id, month)
        total_revenue += result.revenue
        total_cogs += result.cogs
        total_expenses += result.expenses
    
    net = total_revenue - total_cogs - total_expenses
    
    # YTD across all entities
    ytd_revenue = Decimal("0.00")
    ytd_net = Decimal("0.00")
    for entity_id in entity_ids:
        ytd_rev, ytd_n = calc_ytd(entity_id, month)
        ytd_revenue += ytd_rev
        ytd_net += ytd_n
    
    return PNLResult(
        entity_id=UUID(int=0),  # Special marker for consolidated
        month=month,
        revenue=total_revenue,
        cogs=total_cogs,
        expenses=total_expenses,
        net=net,
        ytd_revenue=ytd_revenue,
        ytd_net=ytd_net,
        by_category={},  # Not aggregated in consolidated view
    )


def create_pnl_snapshot(entity_id: UUID, month: date) -> None:
    """
    Create a PNL snapshot for historical tracking.
    
    Args:
        entity_id: Entity UUID
        month: Month to snapshot
    """
    from ..models import PNLSnapshot
    
    result = calc_pnl(entity_id, month)
    
    PNLSnapshot.objects.get_or_create(
        entity_id=entity_id,
        month=month.replace(day=1),
        defaults={
            "revenue": result.revenue,
            "cogs": result.cogs,
            "expenses": result.expenses,
            "net": result.net,
        },
    )
