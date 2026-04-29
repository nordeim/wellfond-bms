"""Customers Routers
===================
Phase 7: Customer DB & Marketing Blast
"""

from ninja import Router

from .customers import router as customers_router

__all__ = ["customers_router"]
