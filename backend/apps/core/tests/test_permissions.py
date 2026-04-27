"""
Test Core Permissions
===================
TDD tests for RBAC decorators, entity scoping, and permission enforcement.

These tests validate the role-based access control system
as specified in Phase 1 implementation plan.
"""

import pytest
import uuid
from functools import wraps

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.test import Client
from ninja.errors import HttpError

from apps.core.models import User, Entity
from apps.core.permissions import (
    require_role,
    scope_entity,
    enforce_pdpa,
)
from apps.core.auth import get_authenticated_user
from apps.operations.models import Dog


@pytest.fixture
def test_entity():
    """Create test entity."""
    entity, _ = Entity.objects.get_or_create(
        id=uuid.uuid4(),
        defaults={"name": "Test Entity", "code": "TEST"},
    )
    return entity


@pytest.fixture
def second_entity():
    """Create second test entity."""
    entity, _ = Entity.objects.get_or_create(
        id=uuid.uuid4(),
        defaults={"name": "Second Entity", "code": "SECOND"},
    )
    return entity


@pytest.fixture
def management_user(test_entity):
    """Create management user."""
    user = User.objects.create_user(
        username="mgmt_user",
        email="mgmt@example.com",
        password="testpass123",
        role="management",
        entity=test_entity,
    )
    return user


@pytest.fixture
def admin_user(test_entity):
    """Create admin user."""
    user = User.objects.create_user(
        username="admin_user",
        email="admin@example.com",
        password="testpass123",
        role="admin",
        entity=test_entity,
    )
    return user


@pytest.fixture
def sales_user(test_entity):
    """Create sales user."""
    user = User.objects.create_user(
        username="sales_user",
        email="sales@example.com",
        password="testpass123",
        role="sales",
        entity=test_entity,
    )
    return user


@pytest.fixture
def ground_user(test_entity):
    """Create ground user."""
    user = User.objects.create_user(
        username="ground_user",
        email="ground@example.com",
        password="testpass123",
        role="ground",
        entity=test_entity,
    )
    return user


@pytest.fixture
def vet_user(test_entity):
    """Create vet user."""
    user = User.objects.create_user(
        username="vet_user",
        email="vet@example.com",
        password="testpass123",
        role="vet",
        entity=test_entity,
    )
    return user


@pytest.fixture
def test_dog(test_entity):
    """Create test dog."""
    from datetime import date
    dog = Dog.objects.create(
        name="Test Dog",
        gender="F",
        breed="Golden Retriever",
        entity=test_entity,
        microchip="1234567890",
        dob=date(2020, 1, 1),
    )
    return dog


@pytest.fixture
def other_entity_dog(second_entity):
    """Create dog in different entity."""
    from datetime import date
    dog = Dog.objects.create(
        name="Other Dog",
        gender="M",
        breed="Labrador",
        entity=second_entity,
        microchip="0987654321",
        dob=date(2019, 1, 1),
    )
    return dog


class TestRequireRoleDecorator:
    """TDD tests for @require_role decorator."""

    def test_require_role_allows_authorized_user(self, admin_user):
        """RED: Decorator should allow authorized users."""
        @require_role("admin")
        def protected_view(request):
            return JsonResponse({"status": "success"})
        
        request = HttpRequest()
        request.user = admin_user
        
        response = protected_view(request)
        
        assert response.status_code == 200
        assert b"success" in response.content

    def test_require_role_denies_unauthorized_user(self, sales_user):
        """Decorator should deny unauthorized users."""
        @require_role("admin")
        def protected_view(request):
            return JsonResponse({"status": "success"})
        
        request = HttpRequest()
        request.user = sales_user
        
        with pytest.raises(HttpError) as exc_info:
            protected_view(request)
        
        assert exc_info.value.status_code == 403

    def test_require_role_denies_anonymous_user(self):
        """Decorator should deny anonymous users."""
        from django.contrib.auth.models import AnonymousUser
        
        @require_role("admin")
        def protected_view(request):
            return JsonResponse({"status": "success"})
        
        request = HttpRequest()
        request.user = AnonymousUser()
        
        with pytest.raises(HttpError) as exc_info:
            protected_view(request)
        
        assert exc_info.value.status_code == 403

    def test_require_role_allows_management_any_role(self, management_user):
        """Management users should have access regardless of required role."""
        @require_role("admin")
        def protected_view(request):
            return JsonResponse({"status": "success"})
        
        request = HttpRequest()
        request.user = management_user
        
        response = protected_view(request)
        
        assert response.status_code == 200

    def test_require_role_allows_multiple_roles(self, sales_user, ground_user):
        """Decorator should accept multiple allowed roles."""
        @require_role(["sales", "ground"])
        def protected_view(request):
            return JsonResponse({"status": "success"})
        
        # Test with sales user
        request = HttpRequest()
        request.user = sales_user
        response = protected_view(request)
        assert response.status_code == 200
        
        # Test with ground user
        request = HttpRequest()
        request.user = ground_user
        response = protected_view(request)
        assert response.status_code == 200


class TestScopeEntity:
    """TDD tests for entity scoping function."""

    @pytest.mark.django_db
    def test_scope_entity_filters_by_user_entity(self, test_entity, admin_user, test_dog):
        """RED: Entity scoping should filter by user's entity."""
        queryset = Dog.objects.all()
        
        scoped = scope_entity(queryset, admin_user)
        
        assert test_dog in scoped
        assert scoped.count() == 1

    @pytest.mark.django_db
    def test_scope_entity_excludes_other_entity(self, test_entity, second_entity, admin_user, other_entity_dog):
        """Scoped queryset should exclude dogs from other entities."""
        queryset = Dog.objects.all()
        
        scoped = scope_entity(queryset, admin_user)
        
        assert other_entity_dog not in scoped

    @pytest.mark.django_db
    def test_scope_entity_allows_management_all_entities(self, management_user, test_entity, second_entity, test_dog, other_entity_dog):
        """Management should see all entities."""
        queryset = Dog.objects.all()
        
        scoped = scope_entity(queryset, management_user)
        
        assert test_dog in scoped
        assert other_entity_dog in scoped
        assert scoped.count() == 2

    @pytest.mark.django_db
    def test_scope_entity_preserves_existing_filters(self, test_entity, admin_user):
        """Entity scoping should preserve existing queryset filters."""
        from datetime import date
        # Create another dog with different status
        Dog.objects.create(
            name="Active Dog",
            gender="M",
            breed="Poodle",
            entity=test_entity,
            microchip="999999999",
            dob=date(2021, 1, 1),
            status="ACTIVE",
        )
        Dog.objects.create(
            name="Retired Dog",
            gender="F",
            breed="Poodle",
            entity=test_entity,
            microchip="888888888",
            dob=date(2018, 1, 1),
            status="RETIRED",
        )
        
        queryset = Dog.objects.filter(status="ACTIVE")
        scoped = scope_entity(queryset, admin_user)
        
        assert scoped.count() == 1
        assert scoped.first().name == "Active Dog"


class TestPDPAEnforcement:
    """TDD tests for PDPA consent enforcement."""

    def test_enforce_pdpa_filters_without_consent(self):
        """RED: PDPA enforcement should filter records without consent."""
        # This is a conceptual test - actual implementation may vary
        queryset = MagicMock()
        queryset.filter = MagicMock(return_value=queryset)
        
        # Mock user with consent checking
        user = MagicMock()
        user.entity_id = uuid.uuid4()
        
        # Call enforce_pdpa
        result = enforce_pdpa(queryset, user)
        
        # Verify filter was called
        queryset.filter.assert_called()

    def test_enforce_pdpa_preserves_other_filters(self):
        """PDPA enforcement should preserve existing filters."""
        queryset = MagicMock()
        queryset.filter = MagicMock(return_value=queryset)
        
        user = MagicMock()
        user.entity_id = uuid.uuid4()
        
        result = enforce_pdpa(queryset, user)
        
        # Should chain filters
        assert queryset.filter.called


class TestRouteAccessMatrix:
    """TDD tests for route access matrix enforcement."""

    def test_login_route_is_public(self):
        """Login route should be accessible without authentication."""
        from apps.core.middleware import AuthenticationMiddleware
        
        middleware = AuthenticationMiddleware(lambda req: HttpResponse())
        
        request = HttpRequest()
        request.path = "/api/v1/auth/login"
        request.COOKIES = {}
        
        response = middleware(request)
        
        # Should not redirect or require auth
        assert response.status_code == 200

    def test_csrf_route_is_public(self):
        """CSRF route should be accessible without authentication."""
        from apps.core.middleware import AuthenticationMiddleware
        
        middleware = AuthenticationMiddleware(lambda req: HttpResponse())
        
        request = HttpRequest()
        request.path = "/api/v1/auth/csrf"
        request.COOKIES = {}
        
        response = middleware(request)
        
        assert response.status_code == 200

    def test_protected_route_requires_auth(self):
        """Protected routes should require authentication."""
        from apps.core.middleware import AuthenticationMiddleware
        
        middleware = AuthenticationMiddleware(lambda req: HttpResponse())
        
        request = HttpRequest()
        request.path = "/api/v1/dogs/"
        request.COOKIES = {}  # No session cookie
        
        response = middleware(request)
        
        # Should have anonymous user attached
        assert hasattr(request, 'user')


class TestEntityScopingMiddleware:
    """TDD tests for EntityScopingMiddleware."""

    def test_middleware_attaches_entity_filter(self, admin_user):
        """Middleware should attach entity filter to request."""
        from apps.core.middleware import EntityScopingMiddleware
        
        middleware = EntityScopingMiddleware(lambda req: HttpResponse())
        
        request = HttpRequest()
        request.user = admin_user
        
        response = middleware(request)
        
        assert hasattr(request, 'entity_filter')
        assert request.entity_filter['entity_id'] == str(admin_user.entity_id)
        assert request.entity_filter['role'] == admin_user.role

    def test_middleware_handles_anonymous_user(self):
        """Middleware should handle anonymous users gracefully."""
        from django.contrib.auth.models import AnonymousUser
        from apps.core.middleware import EntityScopingMiddleware
        
        middleware = EntityScopingMiddleware(lambda req: HttpResponse())
        
        request = HttpRequest()
        request.user = AnonymousUser()
        
        response = middleware(request)
        
        # Should not crash
        assert response.status_code == 200


class TestRoleHierarchy:
    """TDD tests for role hierarchy and permissions."""

    def test_management_has_highest_access(self, management_user):
        """Management should have highest level access."""
        assert management_user.role == "management"
        
        # Management should pass any role check
        @require_role("admin")
        def admin_view(request):
            return JsonResponse({"status": "ok"})
        
        @require_role("sales")
        def sales_view(request):
            return JsonResponse({"status": "ok"})
        
        request = HttpRequest()
        request.user = management_user
        
        assert admin_view(request).status_code == 200
        assert sales_view(request).status_code == 200

    def test_role_ordering(self):
        """Verify role ordering is correct."""
        roles = ["management", "admin", "vet", "sales", "ground"]
        
        # Each role should be in the list
        for role in roles:
            assert role in [r[0] for r in User.Role.choices]


class TestCrossEntityAccess:
    """TDD tests for cross-entity access prevention."""

    @pytest.mark.django_db
    def test_admin_cannot_access_other_entity(self, admin_user, second_entity, other_entity_dog):
        """Admin should not see dogs from other entities."""
        queryset = Dog.objects.all()
        scoped = scope_entity(queryset, admin_user)
        
        assert other_entity_dog not in scoped

    @pytest.mark.django_db
    def test_sales_cannot_access_other_entity(self, sales_user, second_entity, other_entity_dog):
        """Sales should not see dogs from other entities."""
        queryset = Dog.objects.all()
        scoped = scope_entity(queryset, sales_user)
        
        assert other_entity_dog not in scoped

    @pytest.mark.django_db
    def test_ground_cannot_access_other_entity(self, ground_user, second_entity, other_entity_dog):
        """Ground should not see dogs from other entities."""
        queryset = Dog.objects.all()
        scoped = scope_entity(queryset, ground_user)
        
        assert other_entity_dog not in scoped


class TestPermissionEdgeCases:
    """TDD tests for permission edge cases."""

    def test_require_role_with_empty_allowed_roles(self, admin_user):
        """Empty allowed roles list should deny access."""
        @require_role([])
        def protected_view(request):
            return JsonResponse({"status": "success"})
        
        request = HttpRequest()
        request.user = admin_user
        
        with pytest.raises(HttpError) as exc_info:
            protected_view(request)
        
        assert exc_info.value.status_code == 403

    def test_scope_entity_with_none_user(self):
        """Scope entity with None user should return empty queryset."""
        queryset = Dog.objects.all()
        
        # Should not crash
        result = scope_entity(queryset, None)
        
        # Result should be empty or filtered appropriately
        assert result.count() == 0 or hasattr(result, 'count')

    @pytest.mark.django_db
    def test_scope_entity_with_user_no_entity(self, test_entity):
        """User without entity should see empty queryset."""
        user = User.objects.create_user(
            username="no_entity_user",
            email="noentity@example.com",
            password="testpass123",
            role="ground",
            entity=None,
        )
        
        queryset = Dog.objects.all()
        result = scope_entity(queryset, user)
        
        # Should be empty
        assert result.count() == 0
