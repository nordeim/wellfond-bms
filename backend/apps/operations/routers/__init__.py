"""
Operations routers package.
"""
from .alerts import router as alerts_router
from .dogs import router as dogs_router
from .health import router as health_router
from .logs import router as logs_router
from .stream import router as stream_router

__all__ = ["alerts_router", "dogs_router", "health_router", "logs_router", "stream_router"]
