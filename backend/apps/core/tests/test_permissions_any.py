"""Test PERM-010: permissions.py uses `Any` (PEP 484), not bare `any`.

FIX-10: `TypeVar("F", bound=Callable[..., any])` is not valid PEP 484.
The correct type is `Callable[..., Any]` with `Any` imported from `typing`.
"""
from typing import Any as TypingAny

import pytest
from django.test import TestCase

from apps.core.permissions import require_role


class TestPermissionsAnyTyping(TestCase):
    """Verify `Any` from `typing` is used, not bare `any`."""

    def test_permissions_uses_typing_any(self):
        """The `Any` type annotation must come from `typing` module."""
        import inspect
        import apps.core.permissions as perms

        src = inspect.getsource(perms)
        lines = src.splitlines()

        # Find TypeVar line
        typevar_lines = [i for i, ln in enumerate(lines) if 'TypeVar("F"' in ln]
        assert len(typevar_lines) > 0, "TypeVar line not found"

        # Check that the file imports `Any` from `typing`
        imports_any = any("from typing import" in ln and "Any" in ln for ln in lines)
        assert imports_any, "`Any` must be imported from `typing`"

        # Check that bare `any` is not used in a type context
        # (We allow it in docstrings/descriptions)
        for i, ln in enumerate(lines):
            if 'TypeVar("F"' in ln:
                assert "Callable[..., any]" not in ln, (
                    "Bare `any` used in TypeVar — must use `Any`"
                )
                assert "Callable[..., Any]" in ln, (
                    "TypeVar must bound to `Callable[..., Any]`"
                )
                break
