"""
Core app routers - Wellfond BMS
================================
Auth and user management API endpoints.
"""

from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .users import router as users_router

__all__ = ["auth_router", "dashboard_router", "users_router"]
