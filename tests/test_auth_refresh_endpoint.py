"""
TDD Test Suite: /api/v1/auth/refresh Endpoint
==============================================
Tests for the session refresh endpoint.
Expected behavior: POST to /api/v1/auth/refresh with valid session cookie
should return refreshed user data and new CSRF token.
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
from django.http import HttpRequest
from unittest.mock import patch, MagicMock

from apps.core.auth import (
    SessionManager,
    AuthenticationService,
    refresh_session,
)
from apps.core.models import User
from apps.core.routers.auth import refresh
from apps.core.schemas import RefreshResponse, UserResponse


class TestRefreshEndpoint(TestCase):
    """TDD tests for /api/v1/auth/refresh endpoint."""

    def setUp(self):
        """Set up test user and request factory."""
        self.factory = RequestFactory()
        self.user = User.objects.first()
        if not self.user:
            self.fail("No test user exists. Run: python manage.py createsuperuser")

    def test_refresh_returns_valid_session(self):
        """
        Test: POST /api/v1/auth/refresh with valid session cookie
        Expected: 200 OK with user data and new CSRF token
        """
        # Arrange: Create a valid session
        request = self.factory.post("/api/v1/auth/refresh")
        session_key, csrf_token = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act: Call refresh_session
        result = refresh_session(request)

        # Assert: Should return dict with user and csrf_token
        self.assertIsNotNone(result, "refresh_session returned None for valid session")
        self.assertIn("user", result, "Result missing 'user' key")
        self.assertIn("csrf_token", result, "Result missing 'csrf_token' key")

    def test_refresh_user_data_matches_schema(self):
        """
        Test: Refresh response user data must match UserResponse schema
        Expected: All required UserResponse fields present
        """
        # Arrange
        request = self.factory.post("/api/v1/auth/refresh")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        result = refresh_session(request)

        # Assert: Verify UserResponse schema compatibility
        user_data = result["user"]
        required_fields = [
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
        for field in required_fields:
            self.assertIn(
                field, user_data, f"User data missing required field: {field}"
            )

    def test_refresh_user_data_pydantic_validation(self):
        """
        Test: User data from refresh must validate against UserResponse schema
        Expected: Pydantic model_validate succeeds
        """
        # Arrange
        request = self.factory.post("/api/v1/auth/refresh")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        result = refresh_session(request)
        user_data = result["user"]

        # Assert: Pydantic validation should succeed
        try:
            # Create a mock user object that matches the dict
            from types import SimpleNamespace

            mock_user = SimpleNamespace(**user_data)
            validated = UserResponse.model_validate(mock_user)
            self.assertIsNotNone(validated)
        except Exception as e:
            self.fail(f"UserResponse validation failed: {e}")

    def test_refresh_with_invalid_session(self):
        """
        Test: POST /api/v1/auth/refresh with invalid/expired session
        Expected: Returns None (handled by router as 401)
        """
        # Arrange: Request with invalid session key
        request = self.factory.post("/api/v1/auth/refresh")
        request.COOKIES = {AuthenticationService.COOKIE_NAME: "invalid-session-key"}

        # Act
        result = refresh_session(request)

        # Assert
        self.assertIsNone(result, "Should return None for invalid session")

    def test_refresh_no_session_cookie(self):
        """
        Test: POST /api/v1/auth/refresh without session cookie
        Expected: Returns None
        """
        # Arrange: Request with no cookies
        request = self.factory.post("/api/v1/auth/refresh")
        request.COOKIES = {}

        # Act
        result = refresh_session(request)

        # Assert
        self.assertIsNone(result, "Should return None when no session cookie")

    def test_refresh_rotates_csrf_token(self):
        """
        Test: Refresh should generate new CSRF token
        Expected: csrf_token in response different from original
        """
        # Arrange
        request = self.factory.post("/api/v1/auth/refresh")
        session_key, original_csrf = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        result = refresh_session(request)

        # Assert
        new_csrf = result["csrf_token"]
        self.assertNotEqual(original_csrf, new_csrf, "CSRF token should be rotated")

    def test_refresh_extends_session_ttl(self):
        """
        Test: Refresh should extend session TTL
        Expected: Session TTL extended after refresh
        """
        # Arrange
        request = self.factory.post("/api/v1/auth/refresh")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act
        refresh_session(request)

        # Assert: Session should still exist after refresh
        session_data = SessionManager.get_session(session_key)
        self.assertIsNotNone(session_data, "Session should be extended and still valid")


class TestRefreshRouterIntegration(TestCase):
    """Integration tests for refresh router endpoint."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.first()
        if not self.user:
            self.fail("No test user exists")

    def test_refresh_router_endpoint(self):
        """
        Test: Full refresh endpoint via router
        Expected: Returns HttpResponse with user data
        """
        # Arrange
        request = self.factory.post("/api/v1/auth/refresh")
        session_key, _ = SessionManager.create_session(self.user, request)
        request.COOKIES = {AuthenticationService.COOKIE_NAME: session_key}

        # Act: Call the router function
        try:
            response = refresh(request)
            self.assertIsNotNone(response)
            self.assertIn("user", response)
            self.assertIn("csrf_token", response)
        except Exception as e:
            self.fail(f"Router refresh raised exception: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
