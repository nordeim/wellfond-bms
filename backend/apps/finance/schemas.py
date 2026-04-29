"""
Finance Pydantic schemas for Wellfond BMS.

Decimal types are preserved as strings in JSON for precision.
"""
import datetime
from decimal import Decimal
from typing import Any, List, Optional, Dict
from uuid import UUID

from ninja import Schema
from pydantic import Field, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Transaction Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class TransactionCreate(Schema):
    """Schema for creating a transaction."""
    type: str = Field(..., pattern=r"^(REVENUE|EXPENSE|TRANSFER)$")
    amount: Decimal = Field(..., gt=Decimal("0"))
    entity_id: UUID
    date: datetime.date
    category: str = Field(..., pattern=r"^(SALE|VET|MARKETING|OPERATIONS|OTHER)$")
    description: Optional[str] = None
    source_agreement_id: Optional[UUID] = None


class TransactionUpdate(Schema):
    """Schema for updating a transaction (partial)."""
    type: Optional[str] = Field(default=None, pattern=r"^(REVENUE|EXPENSE|TRANSFER)$")
    amount: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    date: Optional[datetime.date] = None
    category: Optional[str] = Field(default=None, pattern=r"^(SALE|VET|MARKETING|OPERATIONS|OTHER)$")
    description: Optional[str] = None


class TransactionResponse(Schema):
    """Schema for transaction response."""
    id: UUID
    type: str
    amount: Decimal
    entity_id: UUID
    gst_component: Decimal
    date: datetime.date
    category: str
    description: Optional[str]
    source_agreement_id: Optional[UUID]
    created_at: datetime.datetime


class TransactionList(Schema):
    """Schema for paginated transaction list."""
    items: List[TransactionResponse]
    total: int
    page: int
    per_page: int


# ═══════════════════════════════════════════════════════════════════════════════
# P&L Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class PNLResponse(Schema):
    """Schema for P&L statement response."""
    entity_id: UUID
    month: datetime.date
    revenue: Decimal
    cogs: Decimal
    expenses: Decimal
    net: Decimal
    ytd_revenue: Decimal
    ytd_net: Decimal
    by_category: Dict[str, Decimal]


class PNLSummary(Schema):
    """Simplified P&L summary for dashboard cards."""
    entity_id: UUID
    entity_name: str
    month: datetime.date
    revenue: Decimal
    net: Decimal
    trend_revenue: Decimal  # vs prior month
    trend_net: Decimal  # vs prior month


# ═══════════════════════════════════════════════════════════════════════════════
# GST Report Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class GSTReportResponse(Schema):
    """Schema for GST report response."""
    entity_id: UUID
    entity_name: str
    quarter: str  # Format: "YYYY-QN"
    total_sales: Decimal
    total_gst: Decimal
    transactions: List[TransactionResponse]
    generated_at: datetime.datetime
    generated_by_id: UUID


class GSTSummary(Schema):
    """Simplified GST summary for dashboard."""
    entity_id: UUID
    entity_name: str
    quarter: str
    total_sales: Decimal
    total_gst: Decimal
    status: str  # "PENDING", "SUBMITTED", "OVERDUE"


# ═══════════════════════════════════════════════════════════════════════════════
# Intercompany Transfer Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class IntercompanyCreate(Schema):
    """Schema for creating intercompany transfer."""
    from_entity_id: UUID
    to_entity_id: UUID
    amount: Decimal = Field(..., gt=Decimal("0"))
    date: datetime.date
    description: str = Field(..., min_length=1)


class IntercompanyResponse(Schema):
    """Schema for intercompany transfer response."""
    id: UUID
    from_entity_id: UUID
    from_entity_name: str
    to_entity_id: UUID
    to_entity_name: str
    amount: Decimal
    date: datetime.date
    description: str
    created_by_id: UUID
    created_by_name: str
    created_at: datetime.datetime


class IntercompanyList(Schema):
    """Schema for paginated intercompany transfer list."""
    items: List[IntercompanyResponse]
    total: int
    page: int
    per_page: int


# ═══════════════════════════════════════════════════════════════════════════════
# Finance Export Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class FinanceExportRequest(Schema):
    """Schema for finance export request."""
    entity_id: UUID
    period: str  # "YYYY-MM" for P&L, "YYYY-QN" for GST
    format: str = Field(..., pattern=r"^(EXCEL|CSV)$")


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard/Stats Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class FinanceStatsResponse(Schema):
    """Schema for finance dashboard statistics."""
    entity_id: UUID
    entity_name: str
    current_month_revenue: Decimal
    current_month_net: Decimal
    ytd_revenue: Decimal
    ytd_net: Decimal
    pending_gst_quarter: Optional[str]
    pending_gst_amount: Optional[Decimal]
    last_updated: datetime.datetime


class FinanceAlert(Schema):
    """Schema for finance alerts/warnings."""
    type: str  # "GST_DUE", "NEGATIVE_CASHFLOW", "INTERCOMPANY_MISMATCH"
    severity: str  # "INFO", "WARNING", "CRITICAL"
    message: str
    entity_id: Optional[UUID]
    action_url: Optional[str]


class FinanceDashboardResponse(Schema):
    """Schema for finance dashboard data."""
    stats: FinanceStatsResponse
    alerts: List[FinanceAlert]
    recent_transactions: List[TransactionResponse]
    pnl_chart_data: List[Dict[str, Any]]  # Monthly data for charts
