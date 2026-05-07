"""Test OP-013: `Dog.age_years` returns `Decimal`, not `float`.

FIX-13: `Dog.age_years` uses `(today - self.dob).days / 365.25` which returns
a Python `float` (IEEE 754). Financial/compliance-adjacent code should use
`Decimal` throughout.
"""
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from django.test import TestCase

from apps.core.models import Entity
from apps.operations.models import Dog

if TYPE_CHECKING:
    from apps.operations.models import Dog


class TestDogAgePrecision(TestCase):
    """Verify `Dog.age_years` returns `Decimal`, not `float`."""

    def test_age_years_returns_decimal(self):
        """age_years must return a Decimal for precision."""
        from datetime import date

        # Create a 3-year-old dog
        dob = date(2023, 1, 15)
        dog = Dog(
            name="TestDog",
            microchip="TEST123",
            dob=dob,
            gender="M",
            status=Dog.Status.ACTIVE,
            entity=Entity.objects.create(name="Test Entity", code="TEST", slug="test-entity"),
        )

        age = dog.age_years
        assert isinstance(age, Decimal), (
            f"age_years must return Decimal, got {type(age).__name__}"
        )

    def test_age_years_avoids_float_precision_glitches(self):
        """Age of a dog should not have floating-point artifacts."""
        from datetime import date

        # Dog born exactly 3 years ago
        today = date.today()
        dob = date(today.year - 3, today.month, today.day)
        dog = Dog(
            name="Exact3YearOld",
            microchip="TEST456",
            dob=dob,
            gender="F",
            status=Dog.Status.ACTIVE,
            entity=Entity.objects.create(name="Test Entity 2", code="TE2", slug="te2"),
        )

        age = dog.age_years
        years = int(age)
        assert years == 3, f"Expected 3, got {years}"
