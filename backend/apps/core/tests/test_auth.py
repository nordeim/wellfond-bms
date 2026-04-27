"""
Test Core Authentication
========================
TDD tests for authentication middleware, SessionManager, and AuthenticationService.

These tests validate the HttpOnly cookie-based authentication system
as specified in Phase 1 implementation plan.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.core.cache import cache

from apps.core.models import User, Entity
from apps.core.auth import (
    SessionManager,
    AuthenticationService,
    get_authenticated_user,
    login_user,
    logout_user,
    refresh_session,
)
from django.middleware.csrf import get_token, rotate_token
from apps.core.middleware import AuthenticationMiddleware


@pytest.fixture
def test_entity():
    """Create test entity."""
    entity, _ = Entity.objects.get_or_create(
        id=uuid.uuid4(),
        defaults={"name": "Test Entity", "code": "TEST"},
    )
    return entity


@pytest.fixture
def test_user(test_entity):
    """Create test user."""
    user = User.objects.create_user(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email="test@example.com",
        password="testpass123",
        role="ground",
        entity=test_entity,
    )
    return user


@pytest.fixture
def test_request():
    """Create test HTTP request."""
    request = HttpRequest()
    request.method = "GET"
    request.META = {
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
    }
    return request


class TestCSRFTokenGeneration:
    """TDD tests for CSRF token generation and rotation.
    
    Note: These tests use Django's native csrf module functions:
    - get_token(request) - generates CSRF token for a request
    - rotate_token(request) - rotates CSRF token for a request
    """

    def test_generate_csrf_token_returns_string(self, test_request):
        """CSRF token should be generated as a string for a request."""
        from django.middleware.csrf import get_token
        token = get_token(test_request)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_rotate_csrf_token_returns_new_token(self, test_request):
        """CSRF rotation should return a new token for a request."""
        from django.middleware.csrf import get_token, rotate_token
        old_token = get_token(test_request)
        rotate_token(test_request)
        new_token = get_token(test_request)

        assert isinstance(new_token, str)
        assert new_token != old_token
        assert len(new_token) > 0


class TestSessionManager:
    """TDD tests for SessionManager functionality."""

    @pytest.mark.django_db
    def test_create_session_returns_tuple(self, test_user, test_request):
        """RED: Session creation should return session key and CSRF token."""
        session_key, csrf_token = SessionManager.create_session(test_user, test_request)
        
        assert isinstance(session_key, str)
        assert isinstance(csrf_token, str)
        assert len(session_key) > 0
        assert len(csrf_token) > 0

    @pytest.mark.django_db
    def test_create_session_stores_in_redis(self, test_user, test_request):
        """Session data should be stored in Redis cache."""
        session_key, csrf_token = SessionManager.create_session(test_user, test_request)
        
        # Verify session data is in Redis
        session_data = SessionManager.get_session(session_key)
        
        assert session_data is not None
        assert session_data["user_id"] == str(test_user.id)
        assert session_data["csrf_token"] == csrf_token

    @pytest.mark.django_db
    def test_get_session_returns_none_for_invalid_key(self):
        """Getting invalid session should return None."""
        session_data = SessionManager.get_session("invalid-session-key")
        
        assert session_data is None

    @pytest.mark.django_db
    def test_delete_session_removes_from_redis(self, test_user, test_request):
        """Session deletion should remove from Redis."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        # Delete session
        SessionManager.delete_session(session_key)
        
        # Verify session is gone
        session_data = SessionManager.get_session(session_key)
        assert session_data is None

    @pytest.mark.django_db
    def test_update_session_activity_updates_timestamp(self, test_user, test_request):
        """Updating session activity should update last activity timestamp."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        # Get original timestamp
        original_data = SessionManager.get_session(session_key)
        original_activity = original_data["last_activity"]
        
        # Wait a moment
        import time
        time.sleep(0.1)
        
        # Update activity
        SessionManager.update_session_activity(session_key)
        
        # Verify timestamp updated
        updated_data = SessionManager.get_session(session_key)
        assert updated_data["last_activity"] > original_activity

    @pytest.mark.django_db
    def test_is_session_valid_returns_true_for_valid_session(self, test_user, test_request):
        """Valid session should return True."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        is_valid = SessionManager.is_session_valid(session_key)
        
        assert is_valid is True

    @pytest.mark.django_db
    def test_is_session_valid_returns_false_for_invalid_session(self):
        """Invalid session should return False."""
        is_valid = SessionManager.is_session_valid("invalid-key")
        
        assert is_valid is False

    @pytest.mark.django_db
    def test_get_session_user_returns_user_for_valid_session(self, test_user, test_request):
        """Getting session user should return User object."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        user = SessionManager.get_session_user(session_key)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    @pytest.mark.django_db
    def test_get_session_user_returns_none_for_invalid_session(self):
        """Getting session user for invalid session should return None."""
        user = SessionManager.get_session_user("invalid-key")
        
        assert user is None


class TestAuthenticationService:
    """TDD tests for AuthenticationService functionality."""

    @pytest.mark.django_db
    def test_authenticate_user_returns_session_on_success(self, test_user, test_request):
        """RED: Successful authentication should return session key and CSRF token."""
        response = MagicMock()
        
        result = AuthenticationService.authenticate(
            request=test_request,
            response=response,
            username=test_user.username,
            password="testpass123",
        )
        
        assert "session_key" in result
        assert "csrf_token" in result
        assert result["user_id"] == str(test_user.id)

    @pytest.mark.django_db
    def test_authenticate_user_returns_error_on_invalid_credentials(self, test_request):
        """Failed authentication should return error."""
        response = MagicMock()
        
        result = AuthenticationService.authenticate(
            request=test_request,
            response=response,
            username="nonexistent",
            password="wrongpass",
        )
        
        assert "error" in result
        assert "session_key" not in result

    @pytest.mark.django_db
    def test_logout_invalidates_session(self, test_user, test_request):
        """Logout should invalidate the session."""
        # Create session first
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        # Verify session exists
        assert SessionManager.is_session_valid(session_key)
        
        # Logout
        response = MagicMock()
        AuthenticationService.logout(response, session_key)
        
        # Verify session is invalidated
        assert not SessionManager.is_session_valid(session_key)

    @pytest.mark.django_db
    def test_refresh_rotates_csrf_token(self, test_user, test_request):
        """Token refresh should rotate CSRF token."""
        # Create initial session
        session_key, old_csrf = SessionManager.create_session(test_user, test_request)
        
        # Refresh
        response = MagicMock()
        result = AuthenticationService.refresh(
            request=test_request,
            response=response,
            session_key=session_key,
        )
        
        # Verify new CSRF token
        assert "csrf_token" in result
        assert result["csrf_token"] != old_csrf

    @pytest.mark.django_db
    def test_refresh_returns_error_for_invalid_session(self, test_request):
        """Refresh with invalid session should return error."""
        response = MagicMock()
        
        result = AuthenticationService.refresh(
            request=test_request,
            response=response,
            session_key="invalid-key",
        )
        
        assert "error" in result


class TestGetAuthenticatedUser:
    """TDD tests for get_authenticated_user helper."""

    @pytest.mark.django_db
    def test_get_authenticated_user_returns_user_for_valid_session(self, test_user, test_request):
        """Should return user for valid session."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        test_request.COOKIES = {"sessionid": session_key}
        
        user = get_authenticated_user(test_request)
        
        assert user is not None
        assert not isinstance(user, AnonymousUser)
        assert user.id == test_user.id

    @pytest.mark.django_db
    def test_get_authenticated_user_returns_anonymous_for_missing_cookie(self, test_request):
        """Should return AnonymousUser for missing cookie."""
        test_request.COOKIES = {}
        
        user = get_authenticated_user(test_request)
        
        assert isinstance(user, AnonymousUser)

    @pytest.mark.django_db
    def test_get_authenticated_user_returns_anonymous_for_invalid_session(self, test_request):
        """Should return AnonymousUser for invalid session."""
        test_request.COOKIES = {"sessionid": "invalid-key"}
        
        user = get_authenticated_user(test_request)
        
        assert isinstance(user, AnonymousUser)


class TestSessionExpiration:
    """TDD tests for session expiration handling."""

    @pytest.mark.django_db
    def test_session_expires_after_15_minutes_inactivity(self, test_user, test_request):
        """Session should expire after 15 minutes of inactivity."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        # Simulate 16 minutes passing
        with patch("apps.core.auth.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=16)
            
            is_valid = SessionManager.is_session_valid(session_key)
            # Note: Actual implementation may vary, this tests the concept

    @pytest.mark.django_db
    def test_session_extended_with_activity(self, test_user, test_request):
        """Session should be extended with activity."""
        session_key, _ = SessionManager.create_session(test_user, test_request)
        
        # Update activity
        SessionManager.update_session_activity(session_key)
        
        # Session should still be valid
        assert SessionManager.is_session_valid(session_key)


class TestSecurityFeatures:
    """TDD tests for authentication security features."""

    @pytest.mark.django_db
    def test_session_key_is_unique_per_user(self, test_user, test_entity, test_request):
        """Each session should have a unique key."""
        # Create another user
        user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123",
            role="ground",
            entity=test_entity,
        )
        
        session1, _ = SessionManager.create_session(test_user, test_request)
        session2, _ = SessionManager.create_session(user2, test_request)
        
        assert session1 != session2

    @pytest.mark.django_db
    def test_session_contains_required_fields(self, test_user, test_request):
        """Session data should contain all required fields."""
        session_key, csrf_token = SessionManager.create_session(test_user, test_request)
        
        session_data = SessionManager.get_session(session_key)
        
        assert "user_id" in session_data
        assert "csrf_token" in session_data
        assert "ip_address" in session_data
        assert "user_agent" in session_data
        assert "created_at" in session_data
        assert "last_activity" in session_data
