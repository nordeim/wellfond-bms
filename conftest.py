"""Root-level conftest for Wellfond BMS django-pytest integration."""
import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


def pytest_configure():
    if not settings.configured:
        django.setup()