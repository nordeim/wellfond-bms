"""
Finance router for Wellfond BMS.

Endpoints:
- GET  /finance/pnl           - P&L statement
- GET  /finance/gst           - GST report
- GET  /finance/transactions  - Transaction list
- POST /finance/intercompany  - Create intercompany transfer
- GET  /finance/intercompany  - List intercompany transfers
- GET  /finance/export/pnl    - Export P&L as Excel
- GET  /finance/export/gst    - Export GST as Excel

Base: /api/v1/finance/
Tags: ["finance"]
"""
import datetime
from typing import Any
from uuid import UUID

from django.db.models import Q
from ninja import Router, Query
from ninja.pagination import paginate

from apps.core.auth import get_authenticated_user
from apps.core.permissions import require_role, scope_entity

from ..models import Transaction, IntercompanyTransfer
from ..schemas import (
    TransactionCreate,
    TransactionList,
    TransactionResponse,
    PNLResponse,
    GSTReportResponse,
    IntercompanyCreate,
    IntercompanyResponse,
    IntercompanyList,
)
from ..services.pnl import calc_pnl, get_pnl_consolidated
from ..services.gst_report import gen_gst_report, gen_gst_excel, gen_pnl_excel

router = Router(tags=["finance"])


@router.get("/pnl", response=PNLResponse)
def get_pnl(request, entity_id: UUID | None = None, month: datetime.date | None = None):
    """
    Get P&L statement for entity and month.

    Args:
        entity_id: Entity UUID (optional, uses user's entity if not provided)
        month: First day of month (defaults to current month)

    Returns:
        PNLResponse with revenue, COGS, expenses, net, YTD figures

    Permissions:
        - Management: Can view any entity
        - Other roles: Can only view their assigned entity
    """
    user = get_authenticated_user(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Unauthorized")

    # Determine entity
    if entity_id is None:
        entity_id = user.entity_id

    # Validate access
    if user.role not in ["MANAGEMENT", "ADMIN"] and entity_id != user.entity_id:
        from ninja.errors import HttpError
        raise HttpError(403, "Forbidden: Cannot access other entity's data")

    # Default to current month
    if month is None:
        today = date.today()
        month = datetime.date(today.year, today.month, 1)

    result = calc_pnl(entity_id, month)

    return PNLResponse(
        entity_id=result.entity_id,
        month=result.month,
        revenue=result.revenue,
        cogs=result.cogs,
        expenses=result.expenses,
        net=result.net,
        ytd_revenue=result.ytd_revenue,
        ytd_net=result.ytd_net,
        by_category=result.by_category,
    )


@router.get("/gst", response=GSTReportResponse)
def get_gst_report(
    request,
    entity_id: UUID | None = None,
    quarter: str | None = None,
):
    """
    Get GST report for entity and quarter.

    Args:
        entity_id: Entity UUID (optional, uses user's entity if not provided)
        quarter: Quarter string (e.g., "2026-Q1", defaults to current quarter)

    Returns:
        GSTReportResponse with total sales, GST amount, transactions

    Note:
        Thomson entity returns 0 GST (GST exempt)
    """
    user = get_authenticated_user(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Unauthorized")

    # Determine entity
    if entity_id is None:
        entity_id = user.entity_id

    # Validate access
    if user.role not in ["MANAGEMENT", "ADMIN"] and entity_id != user.entity_id:
        from ninja.errors import HttpError
        raise HttpError(403, "Forbidden: Cannot access other entity's data")

    # Default to current quarter
    if quarter is None:
        today = date.today()
        q = (today.month - 1) // 3 + 1
        quarter = f"{today.year}-Q{q}"

    from apps.core.models import Entity
    entity = Entity.objects.get(id=entity_id)

    result = gen_gst_report(entity_id, quarter)

    return GSTReportResponse(
        entity_id=result.entity_id,
        entity_name=entity.name,
        quarter=result.quarter,
        total_sales=result.total_sales,
        total_gst=result.total_gst,
        transactions=[
            TransactionResponse(
                id=UUID(int=0),  # Placeholder for GST transactions
                type="REVENUE",
                amount=t.value,
                entity_id=entity_id,
                gst_component=t.gst_amount,
                date=t.datetime.date,
                category="SALE",
                description=t.description,
                source_agreement_id=UUID(t.source) if t.source != "Manual" else None,
                created_at=date.today(),
            )
            for t in result.transactions
        ],
        generated_at=date.today(),
        generated_by_id=user.id,
    )


@router.get("/transactions", response=TransactionList)
def list_transactions(
    request,
    entity_id: UUID | None = None,
    type: str | None = None,
    category: str | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    page: int = 1,
    per_page: int = 25,
):
    """
    List transactions with filters and pagination.

    Args:
        entity_id: Filter by entity (optional)
        type: Filter by transaction type (REVENUE/EXPENSE/TRANSFER)
        category: Filter by category (SALE/VET/MARKETING/OPERATIONS/OTHER)
        date_from: Start date filter
        date_to: End date filter
        page: Page number (default: 1)
        per_page: Items per page (default: 25)

    Returns:
        TransactionList with items and total count
    """
    user = get_authenticated_user(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Unauthorized")

    # Build queryset
    queryset = Transaction.objects.all()

    # Apply entity scoping
    queryset = scope_entity(queryset, user)

    # Additional filters
    if entity_id:
        queryset = queryset.filter(entity_id=entity_id)
    if type:
        queryset = queryset.filter(type=type)
    if category:
        queryset = queryset.filter(category=category)
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)

    # Manual pagination (not using @paginate decorator for control)
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    items = queryset.order_by("-date", "-created_at")[start:end]

    return TransactionList(
        items=[TransactionResponse.model_validate(t, from_attributes=True) for t in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/intercompany", response=IntercompanyResponse)
@require_role("MANAGEMENT", "ADMIN")
def create_intercompany_transfer(request, payload: IntercompanyCreate):
    """
    Create an intercompany transfer.

    Args:
        payload: IntercompanyCreate with from_entity_id, to_entity_id, amount, datetime.date, description

    Returns:
        IntercompanyResponse with created transfer details

    Permissions:
        - MANAGEMENT and ADMIN only

    Note:
        Automatically creates balancing Transaction records
    """
    user = get_authenticated_user(request)

    transfer = IntercompanyTransfer.objects.create(
        from_entity_id=payload.from_entity_id,
        to_entity_id=payload.to_entity_id,
        amount=payload.amount,
        date=payload.datetime.date,
        description=payload.description,
        created_by=user,
    )

    return IntercompanyResponse.model_validate(transfer, from_attributes=True)


@router.get("/intercompany", response=IntercompanyList)
def list_intercompany_transfers(
    request,
    entity_id: UUID | None = None,
    page: int = 1,
    per_page: int = 25,
):
    """
    List intercompany transfers.

    Args:
        entity_id: Filter by from_entity or to_entity
        page: Page number
        per_page: Items per page

    Returns:
        IntercompanyList with transfers
    """
    user = get_authenticated_user(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Unauthorized")

    queryset = IntercompanyTransfer.objects.all()

    # Entity scoping - can see transfers involving their entity
    if user.role not in ["MANAGEMENT", "ADMIN"]:
        queryset = queryset.filter(
            Q(from_entity_id=user.entity_id) | Q(to_entity_id=user.entity_id)
        )
    elif entity_id:
        queryset = queryset.filter(
            Q(from_entity_id=entity_id) | Q(to_entity_id=entity_id)
        )

    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    items = queryset.order_by("-date", "-created_at")[start:end]

    return IntercompanyList(
        items=[IntercompanyResponse.model_validate(t, from_attributes=True) for t in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/export/pnl")
def export_pnl_excel(request, entity_id: UUID, month: datetime.date):
    """
    Download P&L statement as Excel file.

    Args:
        entity_id: Entity UUID
        month: First day of month

    Returns:
        Excel file download
    """
    user = get_authenticated_user(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Unauthorized")

    # Validate access
    if user.role not in ["MANAGEMENT", "ADMIN"] and entity_id != user.entity_id:
        from ninja.errors import HttpError
        raise HttpError(403, "Forbidden")

    excel_bytes = gen_pnl_excel(entity_id, month)

    from django.http import HttpResponse
    response = HttpResponse(
        excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="pnl_{month.strftime("%Y-%m")}.xlsx"'
    return response


@router.get("/export/gst")
def export_gst_excel(request, entity_id: UUID, quarter: str):
    """
    Download GST report as Excel file.

    Args:
        entity_id: Entity UUID
        quarter: Quarter string (e.g., "2026-Q1")

    Returns:
        Excel file download
    """
    user = get_authenticated_user(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Unauthorized")

    # Validate access
    if user.role not in ["MANAGEMENT", "ADMIN"] and entity_id != user.entity_id:
        from ninja.errors import HttpError
        raise HttpError(403, "Forbidden")

    excel_bytes = gen_gst_excel(entity_id, quarter)

    from django.http import HttpResponse
    response = HttpResponse(
        excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="gst_{quarter}.xlsx"'
    return response
