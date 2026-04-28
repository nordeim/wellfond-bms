"""
Auth Router - Wellfond BMS
============================
Authentication endpoints for login/logout/refresh/me.

Rate Limiting:
- Login: 5 attempts per minute per IP
- Refresh: 10 attempts per minute per IP
- CSRF: 20 requests per minute per IP
"""

from ninja import Router
from ninja.errors import HttpError
from django_ratelimit.decorators import ratelimit
from ratelimit.exceptions import Ratelimited

from ..auth import (
    get_authenticated_user,
    login_user,
    logout_user,
    refresh_session,
)
from ..schemas import (
    CsrfResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    UserResponse,
)

router = Router(tags=["auth"])


def ratelimit_handler(exc):
    """Custom rate limit exception handler for Ninja."""
    from django.http import JsonResponse
    return JsonResponse(
        {"error": "Rate limit exceeded", "detail": "Too many requests. Please try again later."},
        status=429
    )


# Apply rate limit decorator to router
router.exception_handler(Ratelimited)(ratelimit_handler)


@router.post("/login")
@ratelimit(key='ip', rate='5/m', method=['POST'])
def login(request, data: LoginRequest):
    """
    Authenticate user and set HttpOnly session cookie.
    
    Rate limit: 5 attempts per minute per IP.

    Returns user data and CSRF token for subsequent requests.
    """
    user, error, response = login_user(request, data.email, data.password)

    if error or not response:
        raise HttpError(401, error or "Login failed")

    return response


@router.post("/logout", response=LogoutResponse)
def logout(request):
    """
    Logout user and clear session cookie.
    """
    return logout_user(request)


@router.post("/refresh", response=RefreshResponse)
@ratelimit(key='ip', rate='10/m', method=['POST'])
def refresh(request):
    """
    Refresh session and rotate CSRF token.
    
    Rate limit: 10 attempts per minute per IP.

    Returns new user data and CSRF token if session is valid.
    """
    result = refresh_session(request)

    if not result:
        raise HttpError(401, "Session expired or invalid")

    return {
        "user": result["user"],
        "csrf_token": result["csrf_token"],
    }


@router.get("/me", response=UserResponse)
def get_me(request):
    """
    Get current authenticated user.

    Returns 401 if not authenticated.
    """
    user = get_authenticated_user(request)

    if not user:
        raise HttpError(401, "Not authenticated")

    return user


@router.get("/csrf", response=CsrfResponse)
@ratelimit(key='ip', rate='20/m', method=['GET'])
def get_csrf(request):
    """
    Get CSRF token for form submissions.
    
    Rate limit: 20 requests per minute per IP.

    This is primarily for frontend initialization.
    Cookie-based auth handles CSRF automatically.
    """
    from django.middleware.csrf import get_token

    return {"csrf_token": get_token(request)}
