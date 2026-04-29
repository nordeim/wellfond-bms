"""Customer Schemas
==================
Phase 7: Customer DB & Marketing Blast

Pydantic v2 schemas for customer operations.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from ninja import Schema


# =============================================================================
# Base Schemas
# =============================================================================

class CustomerBase(Schema):
    """Base customer fields."""

    name: str
    nric: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    address: Optional[str] = None
    housing_type: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(Schema):
    """Create customer request."""

    name: str
    nric: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    address: Optional[str] = None
    housing_type: Optional[str] = None
    entity_id: UUID
    pdpa_consent: bool = False
    notes: Optional[str] = None


class CustomerUpdate(Schema):
    """Update customer request (partial)."""

    name: Optional[str] = None
    nric: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    housing_type: Optional[str] = None
    pdpa_consent: Optional[bool] = None
    notes: Optional[str] = None


class CustomerOut(Schema):
    """Customer response."""

    id: UUID
    name: str
    nric: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    address: Optional[str] = None
    housing_type: Optional[str] = None
    pdpa_consent: bool
    pdpa_consent_date: Optional[datetime] = None
    entity_id: UUID
    entity_name: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CustomerDetailOut(CustomerOut):
    """Customer detail with related data."""

    purchase_history: list[dict] = []
    comms_log: list[dict] = []


# =============================================================================
# List Schemas
# =============================================================================

class CustomerListItem(Schema):
    """Customer list item."""

    id: UUID
    name: str
    mobile: str
    email: Optional[str] = None
    housing_type: Optional[str] = None
    pdpa_consent: bool
    entity_id: UUID
    entity_name: str
    created_at: datetime


class CustomerListResponse(Schema):
    """Paginated customer list."""

    items: list[CustomerListItem]
    total: int
    page: int
    per_page: int


# =============================================================================
# Filter Schemas
# =============================================================================

class CustomerFilters(Schema):
    """Customer list filters."""

    search: Optional[str] = None
    entity_id: Optional[UUID] = None
    pdpa_consent: Optional[bool] = None
    housing_type: Optional[str] = None
    breed: Optional[str] = None  # Filter by purchased breed
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    per_page: int = 25


# =============================================================================
# Segment Schemas
# =============================================================================

class SegmentFilters(Schema):
    """Segment filter criteria."""

    breed: Optional[str] = None
    entity_id: Optional[UUID] = None
    pdpa: Optional[bool] = True  # Default to PDPA consented only
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    housing_type: Optional[str] = None


class SegmentCreate(Schema):
    """Create segment request."""

    name: str
    description: Optional[str] = None
    filters: SegmentFilters
    entity_id: Optional[UUID] = None  # NULL = all entities


class SegmentUpdate(Schema):
    """Update segment request."""

    name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[SegmentFilters] = None


class SegmentOut(Schema):
    """Segment response."""

    id: UUID
    name: str
    description: Optional[str] = None
    filters_json: dict
    customer_count: int
    count_updated_at: Optional[datetime] = None
    entity_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class SegmentPreviewResponse(Schema):
    """Segment preview (count only)."""

    count: int
    filters_applied: dict


# =============================================================================
# Blast Schemas
# =============================================================================

class BlastCreate(Schema):
    """Create blast request."""

    segment_id: Optional[UUID] = None
    customer_ids: Optional[list[UUID]] = None
    channel: Literal["EMAIL", "WA", "BOTH"] = "EMAIL"
    subject: Optional[str] = None
    body: str
    merge_tags: Optional[dict] = None


class BlastProgress(Schema):
    """Blast progress response."""

    blast_id: UUID
    total: int
    sent: int
    delivered: int
    failed: int
    in_progress: bool
    percentage: int


class BlastResult(Schema):
    """Blast send result."""

    blast_id: UUID
    total_recipients: int
    eligible_recipients: int
    excluded_count: int
    channel: str
    status: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None


class BlastPreviewResponse(Schema):
    """Blast preview before sending."""

    total_customers: int
    eligible_customers: int
    excluded_customers: int
    excluded_reason: str
    channel: str
    sample_message: Optional[str] = None


# =============================================================================
# Communication Log Schemas
# =============================================================================

class CommunicationLogOut(Schema):
    """Communication log entry."""

    id: UUID
    customer_id: UUID
    customer_name: str
    campaign_id: str
    blast_id: Optional[UUID] = None
    channel: str
    status: str
    subject: Optional[str] = None
    message_preview: str
    error_message: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class CommunicationLogListResponse(Schema):
    """Paginated communication logs."""

    items: list[CommunicationLogOut]
    total: int
    page: int
    per_page: int


# =============================================================================
# PDPA Consent Schemas
# =============================================================================

class PDPAConsentUpdate(Schema):
    """Update PDPA consent request."""

    consent: bool


class PDPAConsentResponse(Schema):
    """PDPA consent response."""

    customer_id: UUID
    is_consented: bool
    last_updated: Optional[datetime] = None


class PDPABlastEligibility(Schema):
    """Blast eligibility check response."""

    customer_ids: list[UUID]
    eligible_ids: list[UUID]
    excluded_ids: list[UUID]
    eligible_count: int
    excluded_count: int
    exclusion_reason: str


# =============================================================================
# CSV Import Schemas
# =============================================================================

class CSVColumnMapping(Schema):
    """CSV column mapping configuration."""

    name_column: str = "name"
    mobile_column: str = "mobile"
    email_column: Optional[str] = None
    nric_column: Optional[str] = None
    address_column: Optional[str] = None
    housing_type_column: Optional[str] = None
    pdpa_consent_column: Optional[str] = None


class CSVImportRequest(Schema):
    """CSV import request."""

    file_content: str  # Base64 encoded CSV
    column_mapping: CSVColumnMapping
    entity_id: UUID
    skip_duplicates: bool = True


class CSVImportResponse(Schema):
    """CSV import result."""

    imported_count: int
    duplicate_count: int
    error_count: int
    errors: list[dict]


class CSVImportPreview(Schema):
    """CSV import preview before commit."""

    total_rows: int
    valid_rows: int
    duplicate_rows: int
    invalid_rows: int
    sample_data: list[dict]
    column_mapping: CSVColumnMapping
