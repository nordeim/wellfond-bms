"""Sales & AVS Routers — Phase 5."""

from .agreements import router as agreements_router
from .avs import router as avs_router

__all__ = ["agreements_router", "avs_router"]
