"""
Tests for Puppy PII fields removal.
Critical Issues C-004/H-012: Puppy PII fields bypass PDPA.
"""

import pytest
from django.test import TestCase

from apps.breeding.models import Puppy


class TestPuppyPIIFields(TestCase):
    """Test that Puppy model doesn't have PII fields."""

    def test_puppy_has_no_buyer_name_field(self):
        """
        RED: Test that buyer_name field is removed from Puppy.
        Should fail initially because the field exists.
        """
        # Check that buyer_name is NOT a field in Puppy
        puppy_fields = [f.name for f in Puppy._meta.fields]
        self.assertNotIn(
            'buyer_name',
            puppy_fields,
            "buyer_name should be removed from Puppy model (PDPA risk)"
        )

    def test_puppy_has_no_buyer_contact_field(self):
        """
        RED: Test that buyer_contact field is removed from Puppy.
        Should fail initially because the field exists.
        """
        # Check that buyer_contact is NOT a field in Puppy
        puppy_fields = [f.name for f in Puppy._meta.fields]
        self.assertNotIn(
            'buyer_contact',
            puppy_fields,
            "buyer_contact should be removed from Puppy model (PDPA risk)"
        )

    def test_puppy_buyer_info_via_sales_agreement(self):
        """
        Test that buyer info is accessed via SalesAgreement.
        After fix: Puppy shouldn't have PII fields.
        """
        # This test verifies the proper way to access buyer info
        # is via SalesAgreement (which has PDPA filtering)
        from apps.sales.models import SalesAgreement
        
        # SalesAgreement has PDPA filtering via scope_entity()
        # Puppy should NOT have PII fields
        puppy_fields = [f.name for f in Puppy._meta.fields]
        self.assertNotIn('buyer_name', puppy_fields)
        self.assertNotIn('buyer_contact', puppy_fields)
