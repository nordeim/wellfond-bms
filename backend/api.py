"""
Wellfond BMS - Django Ninja API Configuration
==============================================
BFF Security Pattern: HttpOnly cookies, CSRF protection, idempotency keys
"""

from ninja import NinjaAPI
from ninja.security import APIKeyCookie
from ninja.errors import ValidationError
from django.http import JsonResponse


class CookieAuth(APIKeyCookie):
    """
    Security: HttpOnly cookie-based authentication.
    Cookie set by BFF /api/proxy/login endpoint (not accessible to JS).
    """

    param_name = "sessionid"

    def authenticate(self, request, key):
        if request.user.is_authenticated:
            return request.user
        return None


# -----------------------------------------------------------------------------
# Ninja API Instance
# -----------------------------------------------------------------------------
api = NinjaAPI(
    title="Wellfond BMS",
    version="1.0.0",
    description="""
    Breeding Management System for Singapore AVS-licensed operations.

    ## Security
    - All endpoints require authentication via HttpOnly session cookie
    - CSRF tokens required for state-changing operations
    - Idempotency keys supported for POST/PUT/DELETE

    ## Architecture
    - BFF Pattern: Frontend → Next.js API Routes → Django API
    - Cookie-based sessions (HttpOnly, Secure, SameSite=Lax)
    - Rate limiting applied per-user per-endpoint
    """,
    csrf=True,  # Require CSRF token for mutations
    urls_namespace="api",
)


# -----------------------------------------------------------------------------
# Global Exception Handlers
# -----------------------------------------------------------------------------
@api.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    """Handle Pydantic/Django Ninja validation errors."""
    return JsonResponse(
        {"error": "Validation failed", "details": exc.errors}, status=422
    )


@api.exception_handler(Exception)
def server_error_handler(request, exc):
    """Handle unexpected server errors (log, don't leak)."""
    import logging

    logger = logging.getLogger("apps.api")
    logger.exception("Unhandled API exception")
    return JsonResponse(
        {"error": "Internal server error", "reference": request.id}, status=500
    )


# -----------------------------------------------------------------------------
# Router Registration Pattern
# -----------------------------------------------------------------------------
# Routers are registered in each app's urls.py:
#
# from .api import router as breeding_router
# api.add_router("/breeding/", breeding_router, tags=["breeding"])
#
# Example endpoint registration:
# @breeding_router.get("/dogs", response=list[DogSchema])
# def list_dogs(request, entity_id: UUID):
#     return Dog.objects.filter(entity_id=entity_id)
