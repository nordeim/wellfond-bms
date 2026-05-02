"""
Users Router - Wellfond BMS
=============================
User management endpoints (admin only).
"""

from typing import List, Optional
from uuid import UUID

from ninja import Query, Router, Schema
from ninja.errors import HttpError

from apps.core.auth import get_authenticated_user
from ..models import User
from ..schemas import UserCreate, UserResponse, UserUpdate

router = Router(tags=["users"])


class UserListResponse(Schema):
    """Manual pagination response for user list."""

    count: int
    results: List[UserResponse]
    page: int
    per_page: int


def _check_admin_permission(request):
    """Check if user has admin/management permission using session cookie directly."""
    user = get_authenticated_user(request)

    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")

    if user.role not in (User.Role.ADMIN, User.Role.MANAGEMENT):
        raise HttpError(403, "Permission denied: admin role required")

    return user


@router.get("/", response=UserListResponse)
def list_users(request, role: Optional[str] = None, is_active: Optional[bool] = None,
               page: int = 1, per_page: int = 25):
    """
    List all users (admin only) with manual pagination.

    Query params:
    role: Filter by role (management, admin, sales, ground, vet)
    is_active: Filter by active status
    page: Page number (default 1)
    per_page: Items per page (default 25, max 100)
    """
    _check_admin_permission(request)

    per_page = min(per_page, 100)

    queryset = User.objects.all().order_by("-created_at")

    if role:
        queryset = queryset.filter(role=role)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    total_count = queryset.count()
    start = (page - 1) * per_page
    paginated_qs = queryset[start : start + per_page]

    return {
        "count": total_count,
        "results": list(paginated_qs),
        "page": page,
        "per_page": per_page,
    }


@router.get("/{user_id}", response=UserResponse)
def get_user(request, user_id: UUID):
    """Get user by ID (admin only)."""
    _check_admin_permission(request)
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")


@router.post("/", response=UserResponse)
def create_user(request, data: UserCreate):
    """Create new user (admin only)."""
    _check_admin_permission(request)
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already exists")
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username already exists")

    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        mobile=data.mobile or "",
        pdpa_consent=data.pdpa_consent,
    )

    if data.entity_id:
        from ..models import Entity
        try:
            entity = Entity.objects.get(id=data.entity_id)
            user.entity = entity
            user.save()
        except Entity.DoesNotExist:
            raise HttpError(400, "Entity not found")

    return user


@router.patch("/{user_id}", response=UserResponse)
def update_user(request, user_id: UUID, data: UserUpdate):
    """Update user (admin only)."""
    _check_admin_permission(request)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    if data.role is not None:
        user.role = data.role
    if data.mobile is not None:
        user.mobile = data.mobile
    if data.pdpa_consent is not None:
        user.pdpa_consent = data.pdpa_consent
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.entity_id is not None:
        from ..models import Entity
        try:
            entity = Entity.objects.get(id=data.entity_id)
            user.entity = entity
        except Entity.DoesNotExist:
            raise HttpError(400, "Entity not found")

    user.save()
    return user


@router.delete("/{user_id}")
def deactivate_user(request, user_id: UUID):
    """Deactivate user (admin only)."""
    current_user = _check_admin_permission(request)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    if user.id == current_user.id:
        raise HttpError(400, "Cannot deactivate yourself")

    user.is_active = False
    user.save()
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/reset-password")
def reset_password(request, user_id: UUID, new_password: str):
    """Reset user password (admin only)."""
    _check_admin_permission(request)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    user.set_password(new_password)
    user.save()
    return {"message": "Password reset successfully"}