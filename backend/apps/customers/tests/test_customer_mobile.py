"""
Tests for Customer.mobile unique constraint fix.
Critical Issue C-002: unique=True without null=True causes collisions on empty strings.
"""

import uuid
from django.test import TestCase
from django.db import IntegrityError

from apps.core.models import Entity, User
from apps.customers.models import Customer


class TestCustomerMobileConstraint(TestCase):
    """Test that Customer.mobile handles NULL values correctly."""

    def setUp(self):
        """Set up test data."""
        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST", "slug": "test-entity"},
            id=uuid.uuid4(),
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
        )

    def test_two_customers_with_null_mobile(self):
        """
        RED: Test that two customers with mobile=None works.
        Should fail initially because mobile field doesn't have null=True.
        """
        # Create first customer with no mobile
        customer1 = Customer.objects.create(
            name="Customer 1",
            entity=self.entity,
        )
        # Don't set mobile (should be None/null)

        # Create second customer with no mobile
        # This should work after fix (NULL != NULL in SQL)
        try:
            customer2 = Customer.objects.create(
                name="Customer 2",
                entity=self.entity,
            )
            # If we get here, the test passes (NULL values allowed)
            self.assertIsNone(customer2.mobile)
        except IntegrityError:
            # If IntegrityError is raised, the test fails (NULL values not allowed)
            self.fail("IntegrityError raised - mobile field doesn't support NULL values")

    def test_empty_string_mobile_converted_to_null(self):
        """
        Test that empty string mobile is converted to NULL.
        Should fail initially because mobile field doesn't have null=True.
        """
        # Create customer with empty string mobile
        customer = Customer.objects.create(
            name="Customer 3",
            mobile="",  # Empty string
            entity=self.entity,
        )
        
        # After fix, empty string should be converted to NULL
        # This will fail initially because the field doesn't have null=True
        customer.refresh_from_db()
        self.assertIsNone(customer.mobile)
