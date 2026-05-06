"""
Wellfond BMS - Authentication Logic
====================================
HttpOnly cookie-based authentication with Redis sessions.
"""

import uuid
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth import (
    get_user_model,
    login as django_login,
    logout as django_logout,
)
from django.core.cache import caches
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import get_token, rotate_token

User = get_user_model()


class SessionManager:
    """
    Manages Redis-backed sessions for HttpOnly cookie authentication.
    - Access token: 15 minutes
    - Refresh token: 7 days
    - CSRF rotation on login and refresh
    """

    SESSION_KEY_PREFIX = "session:"
    SESSION_DURATION = timedelta(minutes=15)  # Access token
    REFRESH_DURATION = timedelta(days=7)  # Refresh token

    @classmethod
    def _session_cache(cls):
        """Get the dedicated sessions cache backend."""
        return caches["sessions"]

    @classmethod
    def create_session(cls, user: User, request: HttpRequest) -> tuple[str, str]:
        """
        Create a new session for user.
        Returns: (session_key, csrf_token)
        """
        session_key = str(uuid.uuid4())
        csrf_token = get_token(request)

        # Store session in Redis
        session_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "entity_id": str(user.entity_id) if user.entity_id else None,
            "csrf_token": csrf_token,
        }

        session_cache = cls._session_cache()
        session_cache.set(
            cls.SESSION_KEY_PREFIX + session_key,
            session_data,
            timeout=int(cls.SESSION_DURATION.total_seconds()),
        )

        # Also store refresh token (longer duration)
        refresh_key = f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}"
        session_cache.set(
            refresh_key, user.id, timeout=int(cls.REFRESH_DURATION.total_seconds())
        )

        return session_key, csrf_token

    @classmethod
    def get_session(cls, session_key: str) -> Optional[dict]:
        """Get session data from Redis."""
        return cls._session_cache().get(cls.SESSION_KEY_PREFIX + session_key)

    @classmethod
    def extend_session(cls, session_key: str, user: User) -> None:
        """Extend session TTL (called on activity)."""
        session_data = cls.get_session(session_key)
        if session_data:
            cls._session_cache().set(
                cls.SESSION_KEY_PREFIX + session_key,
                session_data,
                timeout=int(cls.SESSION_DURATION.total_seconds()),
            )

    @classmethod
    def delete_session(cls, session_key: str) -> None:
        """Delete session from Redis."""
        session_cache = cls._session_cache()
        session_cache.delete(cls.SESSION_KEY_PREFIX + session_key)
        session_cache.delete(f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}")


class AuthenticationService:
    """
    Authentication service with HttpOnly cookie management.
    """

    COOKIE_NAME = "sessionid"
    COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days

    @classmethod
    def login(
        cls, request: HttpRequest, email: str, password: str
    ) -> tuple[Optional[User], Optional[str], Optional[HttpResponse]]:
        """
        Authenticate user and create session.
        Returns: (user, error_message, response_with_cookie)
        """
        # Django's authenticate uses USERNAME_FIELD which is 'email' for our User model
        user = django_authenticate(request, email=email, password=password)

        if not user:
            return None, "Invalid credentials", None

        if not user.is_active:
            return None, "Account is disabled", None

        # Create session
        session_key, csrf_token = SessionManager.create_session(user, request)

        # Set HttpOnly cookie
        response = JsonResponse(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "entity_id": str(user.entity_id) if user.entity_id else None,
                    "pdpa_consent": user.pdpa_consent,
                },
                "csrf_token": csrf_token,
            }
        )

        # Set HttpOnly session cookie
        response.set_cookie(
            cls.COOKIE_NAME,
            session_key,
            max_age=cls.COOKIE_MAX_AGE,
            httponly=True,
            secure=not settings.DEBUG,  # Secure in production
            samesite="Lax",
            path="/",
        )

        # Rotate CSRF token for security
        rotate_token(request)

        # Log the login
        from .models import AuditLog

        AuditLog.objects.create(
            actor=user,
            action=AuditLog.Action.LOGIN,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return user, None, response

    @classmethod
    def logout(cls, request: HttpRequest) -> HttpResponse:
        """Logout user and clear cookie."""
        session_key = request.COOKIES.get(cls.COOKIE_NAME)

        if session_key:
            # Log the logout
            session_data = SessionManager.get_session(session_key)
            if session_data:
                try:
                    user = User.objects.get(id=session_data["user_id"])
                    from .models import AuditLog

                    AuditLog.objects.create(
                        actor=user,
                        action=AuditLog.Action.LOGOUT,
                        resource_type="user",
                        resource_id=str(user.id),
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    )
                except User.DoesNotExist:
                    pass

            # Delete session
            SessionManager.delete_session(session_key)

        # Clear cookie
        response = JsonResponse({"message": "Logged out successfully"})
        response.delete_cookie(cls.COOKIE_NAME, path="/")

        return response

    @classmethod
    def refresh(cls, request: HttpRequest) -> Optional[dict]:
        """
        Refresh session and rotate CSRF token.
        Returns user data if session is valid.
        """
        session_key = request.COOKIES.get(cls.COOKIE_NAME)

        if not session_key:
            return None

        session_data = SessionManager.get_session(session_key)

        if not session_data:
            return None

        # Get user
        try:
            user = User.objects.get(id=session_data["user_id"])
        except User.DoesNotExist:
            return None

        if not user.is_active:
            return None

        # Extend session
        SessionManager.extend_session(session_key, user)

        # Rotate CSRF token
        rotate_token(request)
        csrf_token = get_token(request)

        return {
            "user": {
                "id": str(user.id),  # Convert UUID to string
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "entity_id": str(user.entity_id) if user.entity_id else None,
                "pdpa_consent": user.pdpa_consent,
                "is_active": user.is_active,
                "created_at": user.created_at,
            },
            "csrf_token": csrf_token,
        }

    @classmethod
    def get_current_user(cls, request: HttpRequest) -> Optional[User]:
        """Get current user from session cookie."""
        session_key = request.COOKIES.get(cls.COOKIE_NAME)

        if not session_key:
            return None

        session_data = SessionManager.get_session(session_key)

        if not session_data:
            return None

        try:
            return User.objects.get(id=session_data["user_id"], is_active=True)
        except User.DoesNotExist:
            return None

    @classmethod
    def get_user_from_request(cls, request: HttpRequest) -> Optional[User]:
        """Alias for get_current_user — used by routers expecting this name."""
        return cls.get_current_user(request)


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def login_user(
    request: HttpRequest, email: str, password: str
) -> tuple[Optional[User], Optional[str], Optional[HttpResponse]]:
    """Public API for login."""
    return AuthenticationService.login(request, email, password)


def logout_user(request: HttpRequest) -> HttpResponse:
    """Public API for logout."""
    return AuthenticationService.logout(request)


def refresh_session(request: HttpRequest) -> Optional[dict]:
    """Public API for session refresh."""
    return AuthenticationService.refresh(request)


def get_authenticated_user(request: HttpRequest) -> Optional[User]:
    """Public API to get current authenticated user."""
    return AuthenticationService.get_current_user(request)
