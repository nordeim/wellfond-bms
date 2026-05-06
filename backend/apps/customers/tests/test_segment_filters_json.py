"""
Test: Segment.filters_json validation.
High Issue H-010: Add Segment.filters_json validation.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from uuid import uuid4

from apps.core.models import Entity
from apps.customers.models import Segment

User = get_user_model()


class TestSegmentFiltersJsonValidation(TestCase):
    """Test filters_json validation in Segment."""

    def setUp(self):
        self.entity = Entity.objects.create(
            name="Test Entity",
            code="TEST",
            slug="test-entity",
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="MARKETING",
        )

    def test_filters_json_must_be_dict(self):
        """RED: Test that filters_json must be a dictionary."""
        # Invalid: should be dict, not list
        segment = Segment(
            name="Test Segment",
            filters_json=["invalid", "list"],  # Should be dict
            created_by=self.user,
        )
        
        # This should raise ValidationError (but currently doesn't)
        with self.assertRaises(ValidationError):
            segment.full_clean()

    def test_filters_json_valid_keys(self):
        """RED: Test that filters_json only allows valid keys."""
        # Invalid keys
        segment = Segment(
            name="Test Segment",
            filters_json={
                "invalid_key": "value",
                "breed": "Labrador",
            },
            created_by=self.user,
        )
        
        # This should raise ValidationError for invalid key
        with self.assertRaises(ValidationError):
            segment.full_clean()

    def test_filters_json_valid_structure(self):
        """GREEN: Test that valid filters_json passes."""
        segment = Segment(
            name="Test Segment",
            filters_json={
                "breed": ["Labrador", "Poodle"],
                "entity": [str(self.entity.id)],
                "pdpa": True,
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-12-31",
                },
                "housing_type": ["HDB", "CONDO"],
            },
            created_by=self.user,
        )
        
        # This should pass validation
        try:
            segment.full_clean()
        except ValidationError:
            self.fail("Valid filters_json raised ValidationError")
