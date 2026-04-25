"""
Wellfond BMS - Pydantic Schemas
=================================
Ninja API schemas for Phase 1.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from .models import User


# =============================================================================
# Auth Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """Login request payload."""

    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=8)


class UserResponse(BaseModel):
    """User data in responses."""

    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    entity_id: Optional[UUID]
    pdpa_consent: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response with user data and CSRF token."""

    user: UserResponse
    csrf_token: str = Field(..., description="CSRF token for subsequent requests")


class RefreshResponse(BaseModel):
    """Session refresh response."""

    user: UserResponse
    csrf_token: str


class LogoutResponse(BaseModel):
    """Logout confirmation."""

    message: str = "Logged out successfully"


# =============================================================================
# User Management Schemas
# =============================================================================


class UserCreate(BaseModel):
    """Create new user (admin only)."""

    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    role: str = Field(..., description="One of: management, admin, sales, ground, vet")
    entity_id: Optional[UUID] = None
    mobile: Optional[str] = None
    pdpa_consent: bool = False

    @validator("role")
    def validate_role(cls, v):
        valid_roles = [
            User.Role.MANAGEMENT,
            User.Role.ADMIN,
            User.Role.SALES,
            User.Role.GROUND,
            User.Role.VET,
        ]
        if v not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        return v


class UserUpdate(BaseModel):
    """Update user (admin only)."""

    role: Optional[str] = None
    entity_id: Optional[UUID] = None
    mobile: Optional[str] = None
    pdpa_consent: Optional[bool] = None
    is_active: Optional[bool] = None

    @validator("role")
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = [
            User.Role.MANAGEMENT,
            User.Role.ADMIN,
            User.Role.SALES,
            User.Role.GROUND,
            User.Role.VET,
        ]
        if v not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        return v


class UserListResponse(BaseModel):
    """Paginated list of users."""

    count: int
    results: list[UserResponse]


# =============================================================================
# Entity Schemas
# =============================================================================


class EntityResponse(BaseModel):
    """Entity data in responses."""

    id: UUID
    name: str
    code: str
    slug: str
    is_active: bool
    is_holding: bool
    gst_rate: float
    avs_license_number: Optional[str]
    avs_license_expiry: Optional[datetime]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    created_at: datetime

    class Config:
        from_attributes = True


class EntityCreate(BaseModel):
    """Create new entity."""

    name: str
    code: str
    slug: str
    gst_rate: float = 0.09
    is_holding: bool = False
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class EntityUpdate(BaseModel):
    """Update entity."""

    name: Optional[str] = None
    is_active: Optional[bool] = None
    avs_license_number: Optional[str] = None
    avs_license_expiry: Optional[datetime] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


# =============================================================================
# Audit Log Schemas
# =============================================================================


class AuditLogEntry(BaseModel):
    """Audit log entry."""

    uuid: UUID
    actor: Optional[UserResponse]
    action: str
    resource_type: str
    resource_id: str
    payload: dict = Field(default_factory=dict)
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""

    count: int
    results: list[AuditLogEntry]


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    details: Optional[str] = None
    reference: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    error: str = "Validation failed"
    details: list[dict] = Field(default_factory=list)


# =============================================================================
# CSRF Schema
# =============================================================================


class CsrfResponse(BaseModel):
    """CSRF token response."""

    csrf_token: str
