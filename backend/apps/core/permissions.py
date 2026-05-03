"""
Wellfond BMS - RBAC Permissions
=================================
Role decorators and entity scoping for Phase 1.
"""

from functools import wraps
from typing import Callable, Optional, Sequence, TypeVar

from django.db.models import QuerySet
from django.http import HttpRequest, JsonResponse

from .models import User

F = TypeVar("F", bound=Callable[..., any])


def require_role(*required_roles: str) -> Callable[[F], F]:
    """
    Decorator that checks if user has any of the required roles.
    Fails closed (returns 403) if user lacks required role.

    Usage:
        @require_role("management", "admin")
        def my_view(request): ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            user = getattr(request, "user", None)

            if not user or not user.is_authenticated:
                return JsonResponse({"error": "Authentication required"}, status=401)

            if not hasattr(user, "role"):
                return JsonResponse({"error": "User role not found"}, status=403)

            if user.role not in required_roles:
                return JsonResponse(
                    {
                        "error": "Permission denied",
                        "required_roles": required_roles,
                        "current_role": user.role,
                    },
                    status=403,
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def scope_entity(queryset: QuerySet, user: User) -> QuerySet:
    """
    Filter queryset by user's entity and enforce PDPA consent.
    MANAGEMENT role sees all entities.
    All other roles see only their assigned entity.

    PDPA: Models with pdpa_consent field are automatically filtered
    to pdpa_consent=True. This is a hard, non-overridable filter per
    compliance requirements.

    Usage:
        dogs = scope_entity(Dog.objects.all(), request.user)
    """
    if not user or not user.is_authenticated:
        return queryset.none()

    # MANAGEMENT sees all
    if user.role != User.Role.MANAGEMENT:
        # Others see only their entity
        if user.entity_id:
            queryset = queryset.filter(entity_id=user.entity_id)
        else:
            return queryset.none()

    # PDPA hard filter — auto-applied for models with pdpa_consent
    if hasattr(queryset.model, "pdpa_consent"):
        queryset = queryset.filter(pdpa_consent=True)

    return queryset


def scope_entity_for_list(
    queryset: QuerySet, user: User, entity_param: Optional[str] = None
) -> QuerySet:
    """
    Scope queryset with optional entity override for MANAGEMENT.
    If user is MANAGEMENT and entity_param is provided, filter by that entity.
    PDPA filter is auto-applied for models with pdpa_consent field.
    """
    if not user or not user.is_authenticated:
        return queryset.none()

    # MANAGEMENT can optionally filter by entity
    if user.role == User.Role.MANAGEMENT:
        if entity_param:
            queryset = queryset.filter(entity_id=entity_param)
    elif user.entity_id:
        queryset = queryset.filter(entity_id=user.entity_id)
    else:
        return queryset.none()

    # PDPA hard filter — auto-applied for models with pdpa_consent
    if hasattr(queryset.model, "pdpa_consent"):
        queryset = queryset.filter(pdpa_consent=True)

    return queryset


def enforce_pdpa(queryset: QuerySet, user: User) -> QuerySet:
    """
    Hard filter for PDPA consent.
    Only returns records where pdpa_consent=True.
    """
    if hasattr(queryset.model, "pdpa_consent"):
        return queryset.filter(pdpa_consent=True)
    return queryset


class PermissionChecker:
    """
    Utility class for checking permissions.
    """

    ROLE_HIERARCHY = {
        User.Role.GROUND: 1,
        User.Role.VET: 1,
        User.Role.SALES: 2,
        User.Role.ADMIN: 3,
        User.Role.MANAGEMENT: 4,
    }

    @classmethod
    def has_role(cls, user: User, *roles: str) -> bool:
        """Check if user has any of the specified roles."""
        if not user or not user.is_authenticated:
            return False
        return user.role in roles

    @classmethod
    def has_higher_or_equal_role(cls, user: User, min_role: str) -> bool:
        """Check if user's role is higher or equal to min_role in hierarchy."""
        if not user or not user.is_authenticated:
            return False

        user_level = cls.ROLE_HIERARCHY.get(user.role, 0)
        min_level = cls.ROLE_HIERARCHY.get(min_role, 999)

        return user_level >= min_level

    @classmethod
    def can_access_entity(cls, user: User, entity_id: str) -> bool:
        """
        Check if user can access data for a specific entity.
        MANAGEMENT can access all entities.
        Others can only access their assigned entity.
        """
        if not user or not user.is_authenticated:
            return False

        if user.role == User.Role.MANAGEMENT:
            return True

        return str(user.entity_id) == str(entity_id) if user.entity_id else False


class RoleGuard:
    """
    Class-based role guard for more complex permission checks.
    """

    # Route access matrix
    ROUTE_ACCESS = {
        # Ground operations
        "/ground/": [User.Role.GROUND, User.Role.MANAGEMENT],
        "/dogs/": [
            User.Role.GROUND,
            User.Role.VET,
            User.Role.SALES,
            User.Role.ADMIN,
            User.Role.MANAGEMENT,
        ],
        # Sales
        "/sales/": [User.Role.SALES, User.Role.ADMIN, User.Role.MANAGEMENT],
        "/waitlist/": [User.Role.SALES, User.Role.ADMIN, User.Role.MANAGEMENT],
        # Breeding
        "/breeding/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        "/studs/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        # Compliance
        "/compliance/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        "/nparks/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        # Finance
        "/finance/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        "/invoices/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        # Customers
        "/customers/": [User.Role.SALES, User.Role.ADMIN, User.Role.MANAGEMENT],
        # Admin/Users
        "/users/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        "/settings/": [User.Role.ADMIN, User.Role.MANAGEMENT],
        # Dashboard
        "/dashboard/": [User.Role.SALES, User.Role.ADMIN, User.Role.MANAGEMENT],
    }

    @classmethod
    def can_access_route(cls, user: User, route: str) -> bool:
        """Check if user can access a specific route."""
        if not user or not user.is_authenticated:
            return False

        # MANAGEMENT can access everything
        if user.role == User.Role.MANAGEMENT:
            return True

        # Find matching route pattern
        for pattern, allowed_roles in cls.ROUTE_ACCESS.items():
            if route.startswith(pattern.replace("/", "")):
                return user.role in allowed_roles

        # Default: deny if no pattern matches
        return False

    @classmethod
    def get_redirect_for_role(cls, role: str) -> str:
        """Get default redirect path for a role."""
        redirects = {
            User.Role.MANAGEMENT: "/dashboard",
            User.Role.ADMIN: "/dashboard",
            User.Role.SALES: "/dashboard",
            User.Role.GROUND: "/ground",
            User.Role.VET: "/dogs",
        }
        return redirects.get(role, "/login")


# Role-based decorators for common patterns
require_management = require_role(User.Role.MANAGEMENT)
require_admin = require_role(User.Role.ADMIN, User.Role.MANAGEMENT)
require_sales = require_role(User.Role.SALES, User.Role.ADMIN, User.Role.MANAGEMENT)
require_ground = require_role(User.Role.GROUND, User.Role.ADMIN, User.Role.MANAGEMENT)
require_vet = require_role(User.Role.VET, User.Role.ADMIN, User.Role.MANAGEMENT)


def require_auth(func: F) -> F:
    """Decorator that requires authentication (any role)."""

    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        return func(request, *args, **kwargs)

    return wrapper


def require_entity_access(func: F) -> F:
    """
    Decorator that attaches entity_filter to request.
    Use with scope_entity() in views.
    """

    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # Attach entity filter to request
        request.entity_filter = {
            "entity_id": user.entity_id if user.entity_id else None,
            "role": user.role,
            "is_management": user.role == User.Role.MANAGEMENT,
        }

        return func(request, *args, **kwargs)

    return wrapper
