"""
TDD Test Suite: /api/v1/users/ Endpoint
=======================================
Tests for the user management endpoints.
Expected behavior: GET /api/v1/users/ with valid admin session
should return paginated list of users.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, "/home/project/wellfond-bms/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import unittest
from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock

from apps.core.auth import SessionManager, AuthenticationService
from apps.core.models import User
from apps.core.routers.users import list_users
from apps.core.permissions import require_admin
from apps.core.schemas import UserResponse


class TestUsersEndpoint(TestCase):
    """TDD tests for /api/v1/users/ endpoint."""

    def setUp(self):
        """Set up test users and request factory."""
        self.factory = RequestFactory()
        # Ensure we have at least one user
        self.user = User.objects.first()
        if not self.user:
            self.fail(
                "No test user exists. Run: python manage.py shell -c \"from apps.core.models import User; User.objects.create_superuser('admin', 'admin@test.com', 'password')\""
            )

    def test_list_users_requires_authentication(self):
        """
        Test: GET /api/v1/users/ without authentication
        Expected: Should fail/reject (401 or permission denied)
        """
        # Arrange: Request without authentication
        request = self.factory.get("/api/v1/users/")
        request.user = MagicMock()
        request.user.is_authenticated = False

        # Act & Assert: Should raise exception or return None
        with self.assertRaises((Exception, AssertionError)):
            list_users(request)

    def test_list_users_requires_admin_role(self):
        """
        Test: GET /api/v1/users/ with non-admin user
        Expected: Should fail with permission error (403)
        """
        # Arrange: Create non-admin user mock
        request = self.factory.get("/api/v1/users/")
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.role = User.Role.GROUND  # Non-admin role

        # Act: Call list_users (should be protected by @require_admin)
        with self.assertRaises((Exception, AssertionError)):
            list_users(request)

    def test_list_users_returns_paginated_response(self):
        """
        Test: GET /api/v1/users/ with admin user
        Expected: Returns paginated response with count and items
        """
        # Arrange: Create authenticated admin request with session cookie
        request = self.factory.get("/api/v1/users/")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        result = list_users(request)

        # Assert: Should return paginated response format
        self.assertIsNotNone(result, "list_users returned None")
        self.assertIn("count", result, "Response missing 'count' field")
        self.assertIn("items", result, "Response missing 'items' field")
        self.assertIsInstance(result["items"], list, "Items should be a list")

    def test_list_users_items_are_user_models(self):
        """
        Test: list_users items should be User model instances
        Expected: items contains User objects
        """
        # Arrange
        request = self.factory.get("/api/v1/users/")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        result = list_users(request)
        items = result["items"]

        # Assert
        self.assertGreater(len(items), 0, "Items list is empty")
        for item in items:
            self.assertIsInstance(
                item, User, f"Item is not a User instance: {type(item)}"
            )

    def test_list_users_items_can_be_serialized(self):
        """
        Test: list_users items must be serializable by UserResponse
        Expected: All items validate against UserResponse schema
        """
        # Arrange
        request = self.factory.get("/api/v1/users/")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        result = list_users(request)
        items = result["items"]

        # Assert: Each item should be serializable
        failed_items = []
        for item in items:
            try:
                # UserResponse.model_validate expects a model or dict with from_attributes=True
                validated = UserResponse.model_validate(item, from_attributes=True)
            except Exception as e:
                failed_items.append((item, str(e)))

        if failed_items:
            errors = "\n".join([f"User {u}: {e}" for u, e in failed_items])
            self.fail(f"Some users failed UserResponse validation:\n{errors}")

    def test_list_users_with_session_cookie(self):
        """
        Test: Full integration test with session cookie
        Expected: Returns paginated users for authenticated admin
        """
        # Arrange: Create session
        request = self.factory.get("/api/v1/users/")
        session_key, csrf = SessionManager.create_session(self.user, request)

        # Simulate cookie-based request
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}
        request.COOKIES = {AuthenticationService.COOKIE_NAME: SessionManager.create_session(self.user, request)[0]}  # Simulate middleware setting user

        # Act
        result = list_users(request)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["count"], User.objects.count())
        self.assertEqual(
            len(result["items"]), min(result["count"], 100)
        )  # Default pagination

    def test_list_users_respects_role_filter(self):
        """
        Test: GET /api/v1/users/?role=management
        Expected: Returns only users with specified role
        """
        # Arrange
        request = self.factory.get("/api/v1/users/", {"role": "management"})
        request.COOKIES = {AuthenticationService.COOKIE_NAME: SessionManager.create_session(self.user, request)[0]}

        # Act
        result = list_users(request)
        items = result["items"]

        # Assert
        for item in items:
            self.assertEqual(
                item.role,
                "management",
                f"User {item.email} has role {item.role}, expected 'management'",
            )

    def test_list_users_respects_active_filter(self):
        """
        Test: GET /api/v1/users/?is_active=true
        Expected: Returns only active users
        """
        # Arrange
        request = self.factory.get("/api/v1/users/", {"is_active": "true"})
        request.COOKIES = {AuthenticationService.COOKIE_NAME: SessionManager.create_session(self.user, request)[0]}

        # Act
        result = list_users(request)
        items = result["items"]

        # Assert
        for item in items:
            self.assertTrue(item.is_active, f"User {item.email} is not active")


class TestUsersPermissions(TestCase):
    """Permission tests for users endpoint."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.first()

    def test_permission_check_allows_management(self):
        """
        Test: _check_admin_permission allows management role
        """
        request = self.factory.get("/api/v1/users/")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Should not raise exception
        try:
            from apps.core.routers.users import _check_admin_permission
            result = _check_admin_permission(request)
            self.assertIsNotNone(result)
            self.assertEqual(result.role, User.Role.MANAGEMENT)
        except Exception as e:
            self.fail(f"Management user should be allowed: {e}")

    def test_permission_check_allows_admin(self):
        """
        Test: _check_admin_permission allows admin role
        """
        # Use existing user (management is also allowed)
        request = self.factory.get("/api/v1/users/")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        try:
            from apps.core.routers.users import _check_admin_permission
            result = _check_admin_permission(request)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Admin user should be allowed: {e}")


class TestUsersEndpointResponseFormat(TestCase):
    """Response format tests for users endpoint."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.first()

    def test_users_response_has_required_fields(self):
        """
        Test: Response must have count and items
        """
        request = self.factory.get("/api/v1/users/")
        request.COOKIES = {AuthenticationService.COOKIE_NAME: SessionManager.create_session(self.user, request)[0]}

        result = list_users(request)

        required_fields = ["count", "items"]
        for field in required_fields:
            self.assertIn(field, result, f"Response missing field: {field}")

    def test_users_items_have_all_user_fields(self):
        """
        Test: Each user item has all required UserResponse fields
        """
        request = self.factory.get("/api/v1/users/")
        request.COOKIES = {AuthenticationService.COOKIE_NAME: SessionManager.create_session(self.user, request)[0]}

        result = list_users(request)
        items = result["items"]

        required_user_fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "entity_id",
            "pdpa_consent",
            "is_active",
            "created_at",
        ]

        for user in items:
            for field in required_user_fields:
                self.assertTrue(
                    hasattr(user, field), f"User {user} missing field: {field}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
