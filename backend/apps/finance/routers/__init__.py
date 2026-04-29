"""
Finance routers for Wellfond BMS.

Base URL: /api/v1/finance/

Routers:
- reports.py: P&L, GST, transactions, intercompany
"""
from .reports import router as finance_router

__all__ = ["finance_router"]
