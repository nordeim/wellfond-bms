"""
Core Middleware - Wellfond BMS
================================
Idempotency + Entity scoping middleware for Phase 1.
"""

import hashlib
import json
from typing import Callable, Optional

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse


class IdempotencyMiddleware:
    """
    Ensures POST/PUT/PATCH/DELETE requests with same idempotency key
    return cached response for 24 hours.

    Header: X-Idempotency-Key: <uuid>

    Special enforcement:
    - POST to /api/v1/operations/logs/ REQUIRES idempotency key
    """

    IDEMPOTENCY_REQUIRED_PATHS = [
        "/api/v1/operations/logs/",
    ]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only process state-changing methods
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return self.get_response(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")

        # Check if idempotency is required for this path
        if self._is_idempotency_required(request.path) and not idempotency_key:
            return JsonResponse(
                {
                    "error": "Idempotency key required",
                    "detail": f"POST to {request.path} requires X-Idempotency-Key header",
                },
                status=400,
            )

        if not idempotency_key:
            return self.get_response(request)

        # Generate cache key from request fingerprint
        fingerprint = self._generate_fingerprint(request, idempotency_key)
        cached_response = cache.get(fingerprint)

        if cached_response:
            # Return cached response with Idempotency-Replay header
            response = JsonResponse(
                cached_response["data"],
                status=cached_response["status"],
            )
            response["Idempotency-Replay"] = "true"
            return response

        # Process request and cache response
        response = self.get_response(request)

        if 200 <= response.status_code < 300:
            try:
                cache.set(
                    fingerprint,
                    {
                        "data": json.loads(response.content),
                        "status": response.status_code,
                    },
                    timeout=86400,  # 24 hours
                )
            except json.JSONDecodeError:
                # Don't cache non-JSON responses
                pass

        return response

    def _generate_fingerprint(self, request: HttpRequest, idempotency_key: str) -> str:
        """Generate unique fingerprint for request."""
        user_id = (
            request.user.id
            if hasattr(request, "user") and request.user.is_authenticated
            else "anon"
        )
        path = request.path
        body = request.body.decode() if request.body else ""

        data = f"{user_id}:{path}:{body}:{idempotency_key}"
        return f"idempotency:{hashlib.sha256(data.encode()).hexdigest()}"

    def _is_idempotency_required(self, path: str) -> bool:
        """Check if idempotency key is required for this path."""
        return any(
            path.startswith(required_path)
            for required_path in self.IDEMPOTENCY_REQUIRED_PATHS
        )


class EntityScopingMiddleware:
    """
    Attaches entity filter to request based on user role/entity.
    Use with scope_entity() in views for automatic entity filtering.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Attach entity filter to request if user is authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            from .models import User

            user = request.user
            request.entity_filter = {
                "entity_id": str(user.entity_id) if user.entity_id else None,
                "role": user.role,
                "is_management": user.role == User.Role.MANAGEMENT,
            }

        return self.get_response(request)


class AuthenticationMiddleware:
    """
    Custom authentication middleware for HttpOnly cookie sessions.
    Attaches user to request from session cookie.
    """

    COOKIE_NAME = "sessionid"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        import sys
        print(f"DEBUG AuthMiddleware: Processing {request.method} {request.path}", file=sys.stderr)
        print(f"DEBUG AuthMiddleware: Cookies: {dict(request.COOKIES)}", file=sys.stderr)

        # Skip for public paths
        if self._is_public_path(request.path):
            print(f"DEBUG AuthMiddleware: Public path, skipping auth", file=sys.stderr)
            return self.get_response(request)

        # Attach user from session cookie
        print(f"DEBUG AuthMiddleware: Authenticating...", file=sys.stderr)
        self._authenticate(request)
        print(f"DEBUG AuthMiddleware: request.user={request.user}, is_authenticated={getattr(request.user, 'is_authenticated', False)}", file=sys.stderr)

        return self.get_response(request)

    def _authenticate(self, request: HttpRequest) -> None:
        """Authenticate user from session cookie."""
        from django.contrib.auth.models import AnonymousUser

        session_key = request.COOKIES.get(self.COOKIE_NAME)

        if not session_key:
            request.user = AnonymousUser()
            return

        # Get session from Redis cache
        from .auth import SessionManager

        session_data = SessionManager.get_session(session_key)

        if not session_data:
            request.user = AnonymousUser()
            return

        # Get user from database
        from .models import User

        try:
            user = User.objects.get(id=session_data["user_id"], is_active=True)
            request.user = user
        except User.DoesNotExist:
            request.user = AnonymousUser()

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        public_paths = [
            "/health/",
            "/ready/",
            "/api/v1/auth/login",
            "/api/v1/auth/csrf",
            "/admin/login/",
        ]
        return any(path.startswith(public) for public in public_paths)
