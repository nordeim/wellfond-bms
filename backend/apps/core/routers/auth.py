"""
Auth Router - Wellfond BMS
============================
Authentication endpoints for login/logout/refresh/me.
"""

from ninja import Router
from ninja.errors import HttpError

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


@router.post("/login", response=LoginResponse)
def login(request, data: LoginRequest):
    """
    Authenticate user and set HttpOnly session cookie.

    Returns user data and CSRF token for subsequent requests.
    """
    user, error = login_user(request, data.username, data.password)

    if error:
        raise HttpError(401, error)

    # Response is built in login_user and attached to request
    # We need to get the CSRF token
    from django.middleware.csrf import get_token

    csrf_token = get_token(request)

    return {
        "user": UserResponse.from_orm(user),
        "csrf_token": csrf_token,
    }


@router.post("/logout", response=LogoutResponse)
def logout(request):
    """
    Logout user and clear session cookie.
    """
    return logout_user(request)


@router.post("/refresh", response=RefreshResponse)
def refresh(request):
    """
    Refresh session and rotate CSRF token.

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
def get_csrf(request):
    """
    Get CSRF token for form submissions.

    This is primarily for frontend initialization.
    Cookie-based auth handles CSRF automatically.
    """
    from django.middleware.csrf import get_token

    return {"csrf_token": get_token(request)}
