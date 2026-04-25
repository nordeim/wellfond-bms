"""
Users Router - Wellfond BMS
=============================
User management endpoints (admin only).
"""

from typing import List, Optional
from uuid import UUID

from ninja import Query, Router
from ninja.errors import HttpError
from ninja.pagination import paginate

from ..models import User
from ..permissions import require_admin
from ..schemas import UserCreate, UserResponse, UserUpdate

router = Router(tags=["users"])


@router.get("/", response=list[UserResponse])
@paginate
@require_admin
def list_users(request, role: Optional[str] = None, is_active: Optional[bool] = None):
    """
    List all users (admin only).

    Query params:
        role: Filter by role (management, admin, sales, ground, vet)
        is_active: Filter by active status
    """
    queryset = User.objects.all().order_by("-created_at")

    if role:
        queryset = queryset.filter(role=role)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset


@router.get("/{user_id}", response=UserResponse)
@require_admin
def get_user(request, user_id: UUID):
    """Get user by ID (admin only)."""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")


@router.post("/", response=UserResponse)
@require_admin
def create_user(request, data: UserCreate):
    """
    Create new user (admin only).

    Sets temporary password, user must change on first login.
    """
    # Check for duplicate email
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already exists")

    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username already exists")

    # Create user
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

    # Set entity if provided
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
@require_admin
def update_user(request, user_id: UUID, data: UserUpdate):
    """Update user (admin only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    # Update fields
    if data.role is not None:
        user.role = data.role
    if data.mobile is not None:
        user.mobile = data.mobile
    if data.pdpa_consent is not None:
        user.pdpa_consent = data.pdpa_consent
    if data.is_active is not None:
        user.is_active = data.is_active

    # Update entity
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
@require_admin
def deactivate_user(request, user_id: UUID):
    """
    Deactivate user (admin only).

    Soft delete - sets is_active=False.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    # Prevent deactivating yourself
    if user.id == request.user.id:
        raise HttpError(400, "Cannot deactivate yourself")

    user.is_active = False
    user.save()

    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/reset-password")
@require_admin
def reset_password(request, user_id: UUID, new_password: str):
    """Reset user password (admin only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    user.set_password(new_password)
    user.save()

    return {"message": "Password reset successfully"}
