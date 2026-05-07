"""Test FIN-012: Finance routers use `Optional[T]`, not `T | None`.

FIX-12: `reports.py` uses `UUID | None = None` and `str | None = None` (9 occurrences).
Per AGENTS.md, must use `Optional[T]` for Pydantic v2 compatibility.
"""
import inspect
import re

import pytest
from django.test import TestCase

import apps.finance.routers.reports as reports_module


class TestFinanceRouterTyping(TestCase):
    """Verify finance routers use `Optional[T]`, not `T | None`."""

    def test_no_union_none_in_finance_routers(self):
        """No `T | None` should appear in finance router function signatures."""
        src = inspect.getsource(reports_module)

        # Find all function signatures
        pattern = re.compile(r"def \w+\([^)]*\)")
        sigs = pattern.findall(src)

        violations = []
        for sig in sigs:
            if " | None" in sig or " |None" in sig:
                violations.append(sig)

        assert len(violations) == 0, (
            f"Found `T | None` in signatures — use `Optional[T]`: {violations}"
        )

    def test_optional_import_present(self):
        """`Optional` must be imported from typing."""
        src = inspect.getsource(reports_module)
        assert "from typing import" in src and "Optional" in src, (
            "`Optional` must be imported from `typing`"
        )
