"""Test CORE-011: CharFields must have `default=''` to avoid NotNullViolation.

FIX-11: Three CharFields in `core/models.py` have `blank=True` but no `default`:
  - `User.mobile` (line 39)
  - `Entity.avs_license_number` (line 109)
  - `Entity.phone` (line 122)
"""
import pytest
from django.test import TestCase

from apps.core.models import User, Entity


class TestCharfieldDefaults(TestCase):
    """Verify CharFields with `blank=True` also have `default=''`."""

    def test_user_mobile_has_default(self):
        """User.mobile must have default=''."""
        field = User._meta.get_field("mobile")
        assert field.default == "", "User.mobile must have default=''"

    def test_entity_avs_license_number_has_default(self):
        """Entity.avs_license_number must have default=''."""
        field = Entity._meta.get_field("avs_license_number")
        assert field.default == "", "Entity.avs_license_number must have default=''"

    def test_entity_phone_has_default(self):
        """Entity.phone must have default=''."""
        field = Entity._meta.get_field("phone")
        assert field.default == "", "Entity.phone must have default=''"
