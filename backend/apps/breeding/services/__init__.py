"""
Breeding & Genetics Services
============================
Phase 4: Breeding & Genetics Engine

Services for COI calculation, saturation analysis, and closure table management.
"""

from .coi import calc_coi, get_shared_ancestors
from .saturation import calc_saturation

__all__ = ["calc_coi", "get_shared_ancestors", "calc_saturation"]
