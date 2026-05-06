"""Test ALERTS-004: django.db.models import should be at top of file.

FIX-04: `from django.db import models` is at line 243 (bottom) in alerts.py,
but `models.Q` is used at line 224. While Python handles this at runtime
(import executes at module load before function is called), it violates
PEP 8 (imports at top) and is fragile to refactoring.
"""
import pytest
from django.test import TestCase

import apps.operations.services.alerts as alerts_module


class TestAlertsImportOrdering(TestCase):
    """Verify imports are at the top of the file."""

    def test_django_models_import_not_at_bottom(self):
        """`from django.db import models` must NOT appear at the bottom."""
        # Read the source file and count lines before first function / import
        import inspect
        import re

        src = inspect.getsource(alerts_module)
        lines = src.splitlines()

        # Find where the django.db import happens
        import_lines = [i for i, line in enumerate(lines) if "from django.db import models" in line]
        if not import_lines:
            pytest.skip("django.db import not present")

        import_idx = import_lines[-1]

        # Count lines that are pure imports before the first def / class
        first_def = len(lines)
        for i, line in enumerate(lines):
            if re.match(r"^(def |class )", line):
                first_def = i
                break

        # The django.db import should be among the initial imports, not past first def
        assert import_idx < first_def, (
            f"`from django.db import models` at line {import_idx + 1} "
            f"should be before first function/class at line {first_def + 1})"
        )
