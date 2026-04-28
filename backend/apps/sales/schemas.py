"""Sales Agreement Pydantic Schemas — Phase 5."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field


# =============================================================================
# Enums
# =============================================================================

class AgreementTypeSchema(Schema):
    """Agreement type choices."""
    B2C: str = "B2C"
    B2B: str = "B2B"
    REHOME: str = "REHOME"


class AgreementStatusSchema(Schema):
    """Agreement status choices."""
    DRAFT: str = "DRAFT"
    SIGNED: str = "SIGNED"
    COMPLETED: str = "COMPLETED"
    CANCELLED: str = "CANCELLED"


class HousingTypeSchema(Schema):
    """Housing type choices."""
    HDB: str = "HDB"
    CONDO: str = "CONDO"
    LANDED: str = "LANDED"
    OTHER: str = "OTHER"


class PaymentMethodSchema(Schema):
    """Payment method choices."""
    CASH: str = "CASH"
    PAYNOW: str = "PAYNOW"
    BANK_TRANSFER: str = "BANK_TRANSFER"
    CREDIT_CARD: str = "CREDIT_CARD"
    INSTALLMENT: str = "INSTALLMENT"


class AVSStatusSchema(Schema):
    """AVS status choices."""
    PENDING: str = "PENDING"
    SENT: str = "SENT"
    COMPLETED: str = "COMPLETED"
    ESCALATED: str = "ESCALATED"


class SignatureMethodSchema(Schema):
    """Signature method choices."""
    IN_PERSON: str = "IN_PERSON"
    REMOTE: str = "REMOTE"
    PAPER: str = "PAPER"


# =============================================================================
# Buyer Information
# =============================================================================

class BuyerInfo(Schema):
    """Buyer information for agreements."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200)
    nric: str = Field("", max_length=20, description="NRIC/FIN")
    mobile: str = Field(..., pattern=r"^\d{8,15}$")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    address: str = Field(..., min_length=10)
    housing_type: str = Field(..., description="HDB, CONDO, LANDED, OTHER")


class BuyerInfoResponse(Schema):
    """Buyer info response."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    nric: str
    mobile: str
    email: str
    address: str
    housing_type: str


# =============================================================================
# Agreement Schemas
# =============================================================================

class LineItemCreate(Schema):
    """Line item for agreement creation."""
    model_config = ConfigDict(from_attributes=True)

    dog_id: UUID
    price: Decimal = Field(..., ge=Decimal("0.00"))


class LineItemResponse(Schema):
    """Line item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dog_id: UUID
    dog_name: str
    dog_microchip: str
    price: Decimal
    gst_component: Decimal


class AgreementCreate(Schema):
    """Schema for creating a sales agreement."""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., pattern=r"^(B2C|B2B|REHOME)$")
    entity_id: UUID
    dog_ids: List[UUID] = Field(..., min_length=1)
    buyer_info: BuyerInfo
    pricing: dict = Field(..., description="{total_amount, deposit, payment_method}")
    special_conditions: str = Field("", max_length=2000)
    pdpa_consent: bool = Field(False)
    tc_acceptance: bool = Field(False)


class AgreementUpdate(Schema):
    """Schema for updating a draft agreement."""
    model_config = ConfigDict(from_attributes=True)

    buyer_info: Optional[BuyerInfo] = None
    pricing: Optional[dict] = None
    special_conditions: Optional[str] = Field(None, max_length=2000)
    pdpa_consent: Optional[bool] = None
    tc_acceptance: Optional[bool] = None


class AgreementListItem(Schema):
    """List item for agreements."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    status: str
    buyer_name: str
    buyer_mobile: str
    entity_id: UUID
    entity_name: str
    total_amount: Decimal
    deposit: Decimal
    pdf_hash: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: datetime
    line_items: List[LineItemResponse] = []


class AgreementDetail(Schema):
    """Full agreement detail response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    status: str
    entity_id: UUID
    entity_name: str

    # Buyer
    buyer_name: str
    buyer_nric: str
    buyer_mobile: str
    buyer_email: str
    buyer_address: str
    buyer_housing_type: str

    # PDPA
    pdpa_consent: bool

    # Pricing
    total_amount: Decimal
    gst_component: Decimal
    deposit: Decimal
    balance: Decimal
    payment_method: str

    # T&C
    special_conditions: str

    # PDF
    pdf_hash: Optional[str] = None
    pdf_url: Optional[str] = None

    # Signatures
    signed_at: Optional[datetime] = None
    signatures: List["SignatureResponse"] = []

    # AVS
    avs_transfers: List["AVSTransferResponse"] = []

    # Line items
    line_items: List[LineItemResponse] = []

    # Audit
    created_by: str
    created_at: datetime


class AgreementFilters(Schema):
    """Filters for agreement list."""
    model_config = ConfigDict(from_attributes=True)

    type: Optional[str] = None
    status: Optional[str] = None
    entity_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    buyer_mobile: Optional[str] = None


# =============================================================================
# Signature Schemas
# =============================================================================

class SignatureCoordinate(Schema):
    """Single signature coordinate point."""
    model_config = ConfigDict(from_attributes=True)

    x: float
    y: float
    timestamp: int


class SignatureCreate(Schema):
    """Schema for capturing a signature."""
    model_config = ConfigDict(from_attributes=True)

    method: str = Field(..., pattern=r"^(IN_PERSON|REMOTE|PAPER)$")
    coordinates: Optional[List[SignatureCoordinate]] = None
    image_url: Optional[str] = None


class SignatureResponse(Schema):
    """Signature response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    signer_type: str
    method: str
    coordinates: List[dict]
    ip_address: Optional[str] = None
    timestamp: datetime
    image_url: Optional[str] = None


# =============================================================================
# AVS Transfer Schemas
# =============================================================================

class AVSTransferResponse(Schema):
    """AVS transfer response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agreement_id: UUID
    dog_id: UUID
    dog_name: str
    buyer_mobile: str
    status: str
    reminder_sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class AVSTransferCreate(Schema):
    """Schema for creating AVS transfer."""
    model_config = ConfigDict(from_attributes=True)

    agreement_id: UUID
    dog_id: UUID
    buyer_mobile: str


# =============================================================================
# T&C Template Schemas
# =============================================================================

class TCTemplateCreate(Schema):
    """Schema for creating/updating T&C template."""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., pattern=r"^(B2C|B2B|REHOME)$")
    content: str = Field(..., min_length=100, max_length=10000)


class TCTemplateResponse(Schema):
    """T&C template response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    content: str
    version: int
    updated_by: str
    updated_at: datetime


# =============================================================================
# Agreement Actions
# =============================================================================

class SignAgreementRequest(Schema):
    """Request to sign an agreement."""
    model_config = ConfigDict(from_attributes=True)

    signature: SignatureCreate


class SendAgreementRequest(Schema):
    """Request to send agreement (generate PDF and dispatch)."""
    model_config = ConfigDict(from_attributes=True)

    channel: str = Field("email", pattern=r"^(email|whatsapp|both)$")


class AgreementSendResponse(Schema):
    """Response after sending agreement."""
    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    pdf_url: Optional[str] = None
    avs_token: Optional[str] = None


# =============================================================================
# Pagination
# =============================================================================

class PaginatedAgreements(Schema):
    """Paginated agreements response."""
    model_config = ConfigDict(from_attributes=True)

    agreements: List[AgreementListItem]
    total: int
    page: int
    per_page: int
