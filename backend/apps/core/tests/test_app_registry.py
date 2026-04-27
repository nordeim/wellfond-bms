"""
TDD Test: App Registry Integrity
================================
Verifies that all apps registered in INSTALLED_APPS are fully implemented
or properly stubbed. Prevents empty stub apps from being registered.
"""

import importlib
import pytest
from django.conf import settings


def test_all_installed_apps_have_models_or_routers():
    """Every app in INSTALLED_APPS must have implemented models or routers."""
    domain_apps = [
        app for app in settings.INSTALLED_APPS
        if app.startswith("apps.")
    ]

    failed_apps = []

    for app_path in domain_apps:
        has_models = False
        has_routers = False

        try:
            importlib.import_module(f"{app_path}.models")
            has_models = True
        except ImportError:
            pass

        try:
            importlib.import_module(f"{app_path}.routers")
            has_routers = True
        except ImportError:
            pass

        if not has_models and not has_routers:
            failed_apps.append(app_path)

    assert len(failed_apps) == 0, (
        f"Apps with no models or routers (remove from INSTALLED_APPS or implement):\n"
        + "\n".join(f"  - {app}" for app in failed_apps)
    )