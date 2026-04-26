"""
Operations Pydantic schemas for Wellfond BMS
============================================
Phase 2: Domain Foundation - Request/Response schemas
"""

from datetime import date
from typing import List, Optional

from ninja import Schema
from pydantic import Field, field_validator

from apps.core.schemas import EntityResponse


# =============================================================================
# Dog Schemas
# =============================================================================

class DogSummary(Schema):
    """Lightweight dog representation for lists."""

    id: str
    microchip: str = Field(..., pattern=r"^\d{9,15}$")
    name: str
    breed: str
    dob: date
    gender: str = Field(..., pattern=r"^[MF]$")
    colour: Optional[str] = None
    entity_id: str
    status: str
    unit: Optional[str] = None
    dna_status: str
    age_display: str
    rehome_flag: Optional[str] = None


class DogDetail(DogSummary):
    """Full dog representation with relationships."""

    dam_id: Optional[str] = None
    dam_name: Optional[str] = None
    sire_id: Optional[str] = None
    sire_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class DogCreate(Schema):
    """Request schema for creating a dog."""

    microchip: str = Field(..., pattern=r"^\d{9,15}$", description="9-15 digits")
    name: str = Field(..., min_length=1, max_length=100)
    breed: str = Field(..., min_length=1, max_length=100)
    dob: date
    gender: str = Field(..., pattern=r"^[MF]$")
    colour: Optional[str] = Field(None, max_length=50)
    entity_id: str
    status: Optional[str] = Field("ACTIVE")
    dam_chip: Optional[str] = Field(
        None, pattern=r"^\d{9,15}$", description="Mother's microchip"
    )
    sire_chip: Optional[str] = Field(
        None, pattern=r"^\d{9,15}$", description="Father's microchip"
    )
    unit: Optional[str] = Field(None, max_length=50)
    dna_status: Optional[str] = Field("PENDING")
    notes: Optional[str] = None


class DogUpdate(Schema):
    """Request schema for updating a dog (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    breed: Optional[str] = Field(None, min_length=1, max_length=100)
    dob: Optional[date] = None
    colour: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[str] = None
    status: Optional[str] = None
    dam_chip: Optional[str] = Field(
        None, pattern=r"^\d{9,15}$", description="Mother's microchip"
    )
    sire_chip: Optional[str] = Field(
        None, pattern=r"^\d{9,15}$", description="Father's microchip"
    )
    unit: Optional[str] = Field(None, max_length=50)
    dna_status: Optional[str] = None
    notes: Optional[str] = None


class DogListResponse(Schema):
    """Paginated list of dogs."""

    count: int
    results: List[DogSummary]
    page: int
    per_page: int


class DogFilterParams(Schema):
    """Query parameters for filtering dogs."""

    status: Optional[str] = None
    entity: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = Field(None, pattern=r"^[MF]?$")
    search: Optional[str] = Field(None, description="Search chip or name")
    unit: Optional[str] = None


# =============================================================================
# Health Record Schemas
# =============================================================================

class HealthRecordSummary(Schema):
    """Lightweight health record representation."""

    id: str
    date: date
    category: str
    description: str
    temperature: Optional[float] = None
    weight: Optional[float] = None
    vet_name: Optional[str] = None
    photos: List[str] = []
    created_at: str


class HealthRecordCreate(Schema):
    """Request schema for creating a health record."""

    date: date
    category: str = Field(..., pattern=r"^(VET_VISIT|TREATMENT|OBSERVATION|EMERGENCY)$")
    description: str = Field(..., min_length=1)
    temperature: Optional[float] = Field(None, ge=35, le=45)
    weight: Optional[float] = Field(None, ge=0.1, le=100)
    vet_name: Optional[str] = Field(None, max_length=100)
    photos: Optional[List[str]] = []


class HealthRecordListResponse(Schema):
    """List of health records for a dog."""

    count: int
    results: List[HealthRecordSummary]


# =============================================================================
# Vaccination Schemas
# =============================================================================

class VaccinationSummary(Schema):
    """Lightweight vaccination representation."""

    id: str
    vaccine_name: str
    date_given: date
    vet_name: Optional[str] = None
    due_date: Optional[date] = None
    status: str
    days_until_due: Optional[int] = None


class VaccinationCreate(Schema):
    """Request schema for creating a vaccination."""

    vaccine_name: str = Field(..., min_length=1, max_length=100)
    date_given: date
    vet_name: Optional[str] = Field(None, max_length=100)
    due_date: Optional[date] = None  # Auto-calculated if not provided
    notes: Optional[str] = None


class VaccinationWithDueDate(VaccinationSummary):
    """Vaccination with calculated due date info."""

    is_overdue: bool
    is_due_soon: bool  # Due within 30 days


class VaccinationListResponse(Schema):
    """List of vaccinations for a dog."""

    count: int
    results: List[VaccinationWithDueDate]


# =============================================================================
# Photo Schemas
# =============================================================================

class DogPhotoSummary(Schema):
    """Lightweight photo representation."""

    id: str
    url: str
    category: str
    customer_visible: bool
    created_at: str


class DogPhotoCreate(Schema):
    """Request schema for uploading a photo."""

    url: str
    category: Optional[str] = Field("GENERAL", pattern=r"^(PROFILE|HEALTH|BREEDING|GENERAL)$")
    customer_visible: Optional[bool] = False


class DogPhotoListResponse(Schema):
    """List of photos for a dog."""

    count: int
    results: List[DogPhotoSummary]


# =============================================================================
# Dog Detail Response (Combined)
# =============================================================================

class DogDetailResponse(DogDetail):
    """Full dog detail with nested relationships."""

    health_records: List[HealthRecordSummary] = []
    vaccinations: List[VaccinationWithDueDate] = []
    photos: List[DogPhotoSummary] = []
    entity: Optional[EntityResponse] = None


# =============================================================================
# Alert Schemas (for Dashboard)
# =============================================================================

class AlertCard(Schema):
    """Alert card for dashboard."""

    id: str
    type: str  # vaccine_overdue, rehome_overdue, in_heat, etc.
    title: str
    count: int
    trend: int  # +1 (up), -1 (down), 0 (same)
    color: str  # red, yellow, green, blue, pink, orange, navy
    entity_id: Optional[str] = None


class AlertCardsResponse(Schema):
    """Collection of alert cards."""

    alerts: List[AlertCard]


# =============================================================================
# Import Result Schema
# =============================================================================

class ImportError(Schema):
    """Error during CSV import."""

    row: int
    field: Optional[str] = None
    message: str


class ImportResult(Schema):
    """Result of CSV import operation."""

    success_count: int
    error_count: int
    errors: List[ImportError]
    imported_ids: List[str] = []
