"""
Compliance Routers
==================

Django Ninja routers for compliance endpoints.

Routers:
- nparks: NParks submission endpoints
- gst: GST reporting endpoints
- pdpa: PDPA consent endpoints
- tc_templates: T&C template management
"""

from ninja import Router

from .nparks import router as nparks_router
from .gst import router as gst_router
from .pdpa import router as pdpa_router

__all__ = ["nparks_router", "gst_router", "pdpa_router"]
