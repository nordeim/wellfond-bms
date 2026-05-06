"""Test FINANCE-001: reports.py has `from datetime import date` available.

FIX-01: Finance router uses `date.today()` but only imports `datetime` module.
When month/quarter params are omitted, the module-level call to `date.today()`
raises NameError at runtime.
"""
import inspect
from datetime import date

import pytest
from django.test import TestCase

from apps.finance.routers.reports import get_pnl, get_gst_report


class TestReportsDateImport(TestCase):
    """Verify `date` is importable in the finance router."""

    def test_date_name_resolves_in_get_pnl(self):
        """Without `month`, get_pnl must resolve `date.today()` without NameError."""
        # Confirm the function signature accepts no month argument
        sig = inspect.signature(get_pnl)
        assert "month" in sig.parameters
        assert sig.parameters["month"].default is None

        # The crucial assertion: `date` is available in the module namespace.
        # Before FIX-01, this would be a NameError when the function body
        # reached `today = date.today()`.
        import apps.finance.routers.reports as reports_module
        assert "date" in dir(reports_module)

    def test_date_is_not_bare_datetime(self):
        """`date` must be the datetime.date class, NOT the datetime module."""
        from apps.finance.routers.reports import get_pnl
        import apps.finance.routers.reports as reports_module

        module_date = getattr(reports_module, "date", None)
        # Should be the class, not the module
        assert module_date is not None
        assert module_date is date
