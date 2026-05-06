"""
Breeding & Genetics Pydantic v2 Schemas
======================================
Phase 4: Breeding & Genetics Engine

Request/response schemas for COI calculation, mate checking,
breeding records, litters, and puppies.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field


# =============================================================================
# Shared Base Schemas
# =============================================================================

class AncestorInfo(Schema):
    """Information about a shared ancestor in a COI calculation."""
    model_config = ConfigDict(from_attributes=True)

    dog_id: UUID
    name: str
    microchip: str
    relationship: str = Field(..., description="e.g., 'Full Sibling', 'Parent', 'Grandparent'")
    generations_back: int = Field(..., description="Generations from dam/sire to this ancestor")


# =============================================================================
# Mate Checker Schemas
# =============================================================================

class MateCheckRequest(Schema):
    """Request to check COI and saturation for a proposed mating."""
    dam_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    sire1_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    sire2_chip: Optional[str] = Field(None, min_length=9, max_length=15, pattern=r"^\d{9,15}$")


class Verdict(str):
    """Verdict enum for mating compatibility."""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    HIGH_RISK = "HIGH_RISK"


class MateCheckResult(Schema):
    """Result of a COI and saturation check for a proposed mating."""
    model_config = ConfigDict(from_attributes=True)

    dam_id: UUID
    dam_name: str
    sire1_id: UUID
    sire1_name: str
    sire2_id: Optional[UUID] = None
    sire2_name: Optional[str] = None

    coi_pct: float = Field(..., description="Coefficient of Inbreeding percentage")
    saturation_pct: float = Field(..., description="Farm saturation percentage")
    verdict: str = Field(..., description="SAFE, CAUTION, or HIGH_RISK")

    shared_ancestors: List[AncestorInfo] = Field(default_factory=list)
    generation_depth: int = Field(default=5, description="Number of generations analyzed")


class MateCheckResponse(Schema):
    """Full response including dam/sire details and shared ancestors."""
    model_config = ConfigDict(from_attributes=True)

    coi_pct: float = Field(..., ge=0, le=100)
    saturation_pct: float = Field(..., ge=0, le=100)
    verdict: str = Field(..., pattern=r"^(SAFE|CAUTION|HIGH_RISK)$")
    shared_ancestors: List[AncestorInfo] = Field(default_factory=list)


# =============================================================================
# Override Schemas
# =============================================================================

class OverrideCreate(Schema):
    """Schema for creating a mate check override."""
    reason: str = Field(..., min_length=10, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)


class OverrideResponse(Schema):
    """Response schema for mate check overrides."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dam_id: UUID
    dam_name: str
    sire1_id: UUID
    sire1_name: str
    sire2_id: Optional[UUID] = None
    sire2_name: Optional[str] = None

    coi_pct: float
    saturation_pct: float
    verdict: str

    override_reason: str
    override_notes: Optional[str] = None

    staff_name: str
    staff_role: str
    created_at: str


class OverrideHistoryResponse(Schema):
    """Paginated response for override history."""
    model_config = ConfigDict(from_attributes=True)

    overrides: List[OverrideResponse]
    total: int
    page: int
    per_page: int


class OverrideListItem(Schema):
    """List item schema for override history (flat structure)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dam_id: UUID
    dam_name: str
    sire1_id: UUID
    sire1_name: str
    sire2_id: Optional[UUID] = None
    sire2_name: Optional[str] = None
    coi_pct: float
    saturation_pct: float
    verdict: str
    override_reason: str
    override_notes: Optional[str] = None
    staff_name: str
    staff_role: str
    created_at: str


# =============================================================================
# Breeding Record Schemas
# =============================================================================

class BreedingRecordCreate(Schema):
    """Schema for creating a breeding record."""
    dam_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    sire1_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    sire2_chip: Optional[str] = Field(None, min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    date: date
    method: str = Field(default="NATURAL", pattern=r"^(NATURAL|ASSISTED)$")
    notes: Optional[str] = Field(None, max_length=1000)


class BreedingRecordUpdate(Schema):
    """Schema for updating a breeding record."""
    method: Optional[str] = Field(None, pattern=r"^(NATURAL|ASSISTED)$")
    confirmed_sire: Optional[str] = Field(None, pattern=r"^(SIRE1|SIRE2|UNCONFIRMED)$")
    notes: Optional[str] = Field(None, max_length=1000)


class BreedingRecordListItem(Schema):
    """List item for breeding records."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dam_name: str
    dam_microchip: str
    sire1_name: str
    sire1_microchip: str
    sire2_name: Optional[str] = None
    sire2_microchip: Optional[str] = None
    date: date
    expected_whelp_date: Optional[date] = None
    method: str
    confirmed_sire: str
    has_litter: bool


class BreedingRecordDetail(Schema):
    """Detailed breeding record with litter info."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dam_id: UUID
    dam_name: str
    dam_microchip: str
    sire1_id: UUID
    sire1_name: str
    sire1_microchip: str
    sire2_id: Optional[UUID] = None
    sire2_name: Optional[str] = None
    sire2_microchip: Optional[str] = None

    date: date
    expected_whelp_date: Optional[date] = None
    method: str
    confirmed_sire: str
    notes: Optional[str] = None

    created_by_name: Optional[str] = None
    created_at: str
    updated_at: str


# =============================================================================
# Litter Schemas
# =============================================================================

class LitterCreate(Schema):
    """Schema for creating a litter."""
    breeding_record_id: UUID
    whelp_date: date
    delivery_method: str = Field(default="NATURAL", pattern=r"^(NATURAL|C_SECTION)$")
    alive_count: int = Field(default=0, ge=0, le=20)
    stillborn_count: int = Field(default=0, ge=0, le=20)
    notes: Optional[str] = Field(None, max_length=1000)


class LitterUpdate(Schema):
    """Schema for updating a litter."""
    whelp_date: Optional[date] = None
    delivery_method: Optional[str] = Field(None, pattern=r"^(NATURAL|C_SECTION)$")
    alive_count: Optional[int] = Field(None, ge=0, le=20)
    stillborn_count: Optional[int] = Field(None, ge=0, le=20)
    notes: Optional[str] = Field(None, max_length=1000)


class LitterListItem(Schema):
    """List item for litters."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    breeding_record_id: UUID
    dam_name: str
    sire_name: str
    whelp_date: date
    alive_count: int
    stillborn_count: int
    total_count: int
    delivery_method: str
    puppy_count: int


class LitterDetail(Schema):
    """Detailed litter with puppies."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    breeding_record_id: UUID
    dam_id: UUID
    dam_name: str
    dam_microchip: str
    sire1_id: UUID
    sire1_name: str
    sire1_microchip: str
    sire2_id: Optional[UUID] = None
    sire2_name: Optional[str] = None
    sire2_microchip: Optional[str] = None

    whelp_date: date
    delivery_method: str
    alive_count: int
    stillborn_count: int
    total_count: int
    notes: Optional[str] = None

    puppies: List["PuppyListItem"]

    created_by_name: Optional[str] = None
    created_at: str
    updated_at: str


# =============================================================================
# Puppy Schemas
# =============================================================================

class PuppyCreate(Schema):
    """Schema for creating a puppy."""
    litter_id: UUID
    microchip: Optional[str] = Field(None, min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    gender: str = Field(..., pattern=r"^(M|F)$")
    colour: str = Field(..., max_length=50)
    birth_weight: Optional[Decimal] = Field(None, ge=Decimal("0.01"))
    confirmed_sire: Optional[str] = Field("UNCONFIRMED", pattern=r"^(SIRE1|SIRE2|UNCONFIRMED)$")
    paternity_method: Optional[str] = Field("UNCONFIRMED", pattern=r"^(VISUAL|DNA|UNCONFIRMED)$")


class PuppyUpdate(Schema):
    """Schema for updating a puppy."""
    microchip: Optional[str] = Field(None, min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    colour: Optional[str] = Field(None, max_length=50)
    birth_weight: Optional[Decimal] = Field(None, ge=Decimal("0.01"))
    confirmed_sire: Optional[str] = Field(None, pattern=r"^(SIRE1|SIRE2|UNCONFIRMED)$")
    paternity_method: Optional[str] = Field(None, pattern=r"^(VISUAL|DNA|UNCONFIRMED)$")
    status: Optional[str] = Field(None, pattern=r"^(ALIVE|REHOMED|DECEASED)$")
    sale_date: Optional[date] = None


class PuppyListItem(Schema):
    """List item for puppies."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    litter_id: UUID
    microchip: Optional[str] = None
    gender: str
    colour: str
    birth_weight: Optional[Decimal] = None
    confirmed_sire: str
    paternity_method: str
    status: str
    sale_date: Optional[date] = None


class PuppyDetail(Schema):
    """Detailed puppy record."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    litter_id: UUID
    dam_name: str
    sire_name: str
    whelp_date: date

    microchip: Optional[str] = None
    gender: str
    colour: str
    birth_weight: Optional[Decimal] = None
    confirmed_sire: str
    paternity_method: str
    status: str

    sale_date: Optional[date] = None

    created_at: str
    updated_at: str


# =============================================================================
# Filter & Pagination Schemas
# =============================================================================

class BreedingRecordFilters(Schema):
    """Filters for breeding record list."""
    dam_chip: Optional[str] = None
    sire_chip: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    has_litter: Optional[bool] = None


class LitterFilters(Schema):
    """Filters for litter list."""
    dam_chip: Optional[str] = None
    sire_chip: Optional[str] = None
    whelp_date_from: Optional[date] = None
    whelp_date_to: Optional[date] = None


class PaginatedBreedingRecords(Schema):
    """Paginated response for breeding records."""
    model_config = ConfigDict(from_attributes=True)

    records: List[BreedingRecordListItem]
    total: int
    page: int
    per_page: int


class PaginatedLitters(Schema):
    """Paginated response for litters."""
    model_config = ConfigDict(from_attributes=True)

    litters: List[LitterListItem]
    total: int
    page: int
    per_page: int


class PaginatedPuppies(Schema):
    """Paginated response for puppies."""
    model_config = ConfigDict(from_attributes=True)

    puppies: List[PuppyListItem]
    total: int
    page: int
    per_page: int


# =============================================================================
# COI Calculation Schemas
# =============================================================================

class COICalculateRequest(Schema):
    """Request to calculate COI for two dogs."""
    dam_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    sire_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    generations: int = Field(default=5, ge=3, le=10)


class COICalculateResponse(Schema):
    """Response with COI calculation."""
    model_config = ConfigDict(from_attributes=True)

    dam_id: UUID
    dam_name: str
    sire_id: UUID
    sire_name: str
    coi_pct: float = Field(..., ge=0, le=100)
    shared_ancestors: List[AncestorInfo]
    generation_depth: int
    cached: bool = False


class SaturationCalculateRequest(Schema):
    """Request to calculate farm saturation for a sire."""
    sire_chip: str = Field(..., min_length=9, max_length=15, pattern=r"^\d{9,15}$")
    entity_code: Optional[str] = None


class SaturationCalculateResponse(Schema):
    """Response with saturation calculation."""
    model_config = ConfigDict(from_attributes=True)

    sire_id: UUID
    sire_name: str
    entity_id: UUID
    entity_name: str
    saturation_pct: float = Field(..., ge=0, le=100)
    threshold: str = Field(..., pattern=r"^(SAFE|CAUTION|HIGH_RISK)$")
    active_dogs_in_entity: int
    dogs_with_ancestry: int
