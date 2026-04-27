"""
TDD Test: Project-Level Test Discovery
======================================
Verifies that tests can be discovered and executed from the project root
using the project-level pytest.ini configuration.
"""

import importlib
import pytest
from django.conf import settings


def test_django_settings_configured():
    """Django settings are correctly configured from project root."""
    assert settings.configured, "Django settings not configured from root"


def test_installed_apps_contains_core():
    """Core app is in INSTALLED_APPS (validates config loading)."""
    assert "apps.core" in settings.INSTALLED_APPS, (
        "Core app not in INSTALLED_APPS"
    )


def test_pytest_ini_pythonpath_includes_backend():
    """backends/ is in the Python path (validates pythonpath config)."""
    try:
        importlib.import_module("config.settings")
        success = True
    except ImportError:
        success = False
    assert success, "backend/ not in Python path — check pytest.ini pythonpath"