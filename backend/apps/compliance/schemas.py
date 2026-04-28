"""Compliance & NParks Reporting Schemas
=========================================
Phase 6: Compliance & NParks Reporting

Pydantic schemas for API request/response validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field, field_validator


# =============================================================================
# NParks Schemas
# =============================================================================

class NParksGenerateRequest(Schema):
    """Request to generate NParks documents."""
    entity_id: UUID
    month: date = Field(description="First day of reporting month")


class NParksPreviewRow(Schema):
    """Single row in NParks preview table."""
    model_config = ConfigDict(extra="allow")

    row_num: int
    data: dict


class NParksPreview(Schema):
    """Preview of NParks document before generation."""
    doc_type: str = Field(description="Document type: mating_sheet, puppy_movement, etc.")
    headers: list[str]
    rows: list[NParksPreviewRow]
    total_rows: int


class NParksSubmissionResponse(Schema):
    """NParks submission response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_id: UUID
    entity_name: str
    month: date
    status: str
    generated_at: datetime
    submitted_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    generated_by: str

    mating_sheet_ready: bool = False
    puppy_movement_ready: bool = False
    vet_treatments_ready: bool = False
    puppies_bred_ready: bool = False
    dog_movement_ready: bool = False


class NParksListResponse(Schema):
    """Paginated list of NParks submissions."""
    items: list[NParksSubmissionResponse]
    total: int
    page: int
    per_page: int


class NParksSubmitRequest(Schema):
    """Request to submit NParks documents."""
    submission_id: UUID


class NParksLockRequest(Schema):
    """Request to lock NParks submission (irreversible)."""
    submission_id: UUID


class NParksDownloadRequest(Schema):
    """Request to download NParks document."""
    submission_id: UUID
    doc_type: str = Field(description="Document type: mating_sheet, puppy_movement, vet_treatments, puppies_bred, dog_movement")


# =============================================================================
# GST Schemas
# =============================================================================

class GSTSummary(Schema):
    """GST summary for a quarter."""
    entity_id: UUID
    entity_name: str
    quarter: str = Field(description="Format: YYYY-Q#")
    total_sales: Decimal = Field(decimal_places=2)
    total_gst: Decimal = Field(decimal_places=2)
    transactions_count: int


class GSTExportRequest(Schema):
    """Request to export GST ledger."""
    entity_id: UUID
    quarter: str = Field(description="Format: YYYY-Q#")


class GSTLedgerEntry(Schema):
    """Single GST ledger entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agreement_id: UUID
    agreement_number: str
    buyer_name: str
    total_sales: Decimal = Field(decimal_places=2)
    gst_component: Decimal = Field(decimal_places=2)
    created_at: datetime


class GSTLedgerResponse(Schema):
    """Paginated GST ledger entries."""
    items: list[GSTLedgerEntry]
    total: int
    page: int
    per_page: int


class GSTCalculationRequest(Schema):
    """Request to calculate GST."""
    price: Decimal = Field(decimal_places=2, ge=Decimal("0"))
    entity_id: UUID


class GSTCalculationResponse(Schema):
    """GST calculation result."""
    price: Decimal = Field(decimal_places=2)
    gst_rate: Decimal = Field(decimal_places=4)
    gst_component: Decimal = Field(decimal_places=2)
    subtotal: Decimal = Field(decimal_places=2)
    total: Decimal = Field(decimal_places=2)


# =============================================================================
# PDPA Schemas
# =============================================================================

class PDPAConsentUpdate(Schema):
    """Request to update PDPA consent."""
    customer_id: UUID
    action: str = Field(description="OPT_IN or OPT_OUT")

    @field_validator("action")
    def validate_action(cls, v: str) -> str:
        if v not in ("OPT_IN", "OPT_OUT"):
            raise ValueError("action must be OPT_IN or OPT_OUT")
        return v


class PDPAConsentLogEntry(Schema):
    """PDPA consent log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    action: str
    previous_state: bool
    new_state: bool
    actor: str
    ip_address: Optional[str] = None
    created_at: datetime


class PDPAConsentLogResponse(Schema):
    """Paginated PDPA consent log entries."""
    items: list[PDPAConsentLogEntry]
    total: int
    page: int
    per_page: int


class PDPAConsentCheckRequest(Schema):
    """Request to check blast eligibility."""
    customer_ids: list[UUID]


class PDPAConsentCheckResponse(Schema):
    """Blast eligibility check result."""
    eligible_ids: list[UUID]
    excluded_ids: list[UUID]
    eligible_count: int
    excluded_count: int
    exclusion_reason: str = Field(default="PDPA consent not granted")


# =============================================================================
# T&C Template Schemas
# =============================================================================

class TCTemplateUpdate(Schema):
    """Request to update T&C template."""
    template_type: str = Field(description="B2C, B2B, or REHOME")
    content: str

    @field_validator("template_type")
    def validate_type(cls, v: str) -> str:
        if v not in ("B2C", "B2B", "REHOME"):
            raise ValueError("template_type must be B2C, B2B, or REHOME")
        return v


class TCTemplateResponse(Schema):
    """T&C template response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    content: str
    version: int
    updated_by: str
    updated_at: datetime


class TCTemplateListResponse(Schema):
    """List of T&C templates."""
    items: list[TCTemplateResponse]
    total: int


class TCTemplatePreviewRequest(Schema):
    """Request to preview T&C template with variables."""
    template_type: str
    variables: dict = Field(default_factory=dict)


class TCTemplatePreviewResponse(Schema):
    """Preview of rendered T&C template."""
    template_type: str
    rendered_content: str
    variables_used: list[str]
