"""
Breeding & Genetics Routers
============================
Phase 4: Breeding & Genetics Engine

Router registration for breeding endpoints.
"""

from .mating import router as mating_router
from .litters import router as litters_router

__all__ = ["mating_router", "litters_router"]
