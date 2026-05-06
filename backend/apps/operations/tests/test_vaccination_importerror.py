"""
Test: Vaccination.save() ImportError catch.
High Issue H-006: Fix Vaccination.save() broad ImportError catch.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.core.models import Entity
from apps.operations.models import Dog, Vaccination

User = get_user_model()


class TestVaccinationImportErrorCatch(TestCase):
    """Test that ImportError catch is not too broad."""

    def setUp(self):
        self.entity = Entity.objects.create(
            name="Test Entity",
            code="TEST",
            slug="test-entity",
        )
        self.dog = Dog.objects.create(
            microchip="900001234567890",
            name="Test Dog",
            breed="Labrador",
            dob="2024-01-01",
            gender="M",
            entity=self.entity,
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="GROUND",
        )

    def test_importerror_only_catches_import_failure(self):
        """RED: Test that ImportError only catches import failure, not calc_vaccine_due errors."""
        # This test verifies that the try-except block ONLY wraps the import statement
        # Currently, it wraps both import and calc_vaccine_due() call
        
        # Create vaccination
        vacc = Vaccination(
            dog=self.dog,
            vaccine_name="Parvo",
            date_given="2024-01-01",
            created_by=self.user,
        )
        
        # Mock calc_vaccine_due to raise ImportError
        # With current code (broad catch), this will be caught
        # With fix (only import in try-except), this should propagate
        with patch('apps.operations.services.vaccine.calc_vaccine_due', side_effect=ImportError("Mock import error")):
            # This should raise ImportError (not catch it)
            # With current code, it's caught (logged) and save() continues
            try:
                vacc.save()
                # If we get here, the error was caught (broad catch)
                # This is the bug - we want the test to fail here
                self.fail("ImportError was caught - broad catch detected")
            except ImportError as e:
                # Error propagated - this is the expected behavior after fix
                self.assertIn("Mock import error", str(e))

    def test_due_date_calculated_when_import_succeeds(self):
        """Test that due date is calculated when import succeeds."""
        from datetime import date
        
        vacc = Vaccination(
            dog=self.dog,
            vaccine_name="Parvo",
            date_given="2024-01-01",
            created_by=self.user,
        )
        
        # Mock calc_vaccine_due to return a date object
        with patch('apps.operations.services.vaccine.calc_vaccine_due', return_value=date(2024, 2, 1)):
            vacc.save()
        
        # Due date should be set
        self.assertEqual(vacc.due_date, date(2024, 2, 1))
