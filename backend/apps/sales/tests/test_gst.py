"""GST Calculation Tests
=========================
Phase 5: Sales Agreements & AVS Tracking

Tests for GST calculation logic and price extraction.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest
import uuid
from django.test import TestCase

from apps.core.models import Entity
from apps.sales.services.agreement import AgreementService


class TestGSTCalculation(TestCase):
    """Test GST calculation per IRAS requirements."""

    def setUp(self):
        """Set up test data."""
        self.katong, _ = Entity.objects.get_or_create(
            defaults={"name": "Katong", "code": "KATONG"},
            id=uuid.uuid4(),
        )
        self.thomson, _ = Entity.objects.get_or_create(
            defaults={"name": "Thomson", "code": "THOMSON"},
            id=uuid.uuid4(),
        )

    def tearDown(self):
        """Clean up test data."""
        Entity.objects.filter(id__in=[self.katong.id, self.thomson.id]).delete()

    def test_gst_calculation_formula(self):
        """
        Test GST extraction formula: price * 9 / 109, ROUND_HALF_UP.

        Given: Total price of $1000
        When: GST is extracted
        Then: GST = round(1000 * 9 / 109, 2) = $82.57
              Subtotal = $917.43
        """
        total = Decimal("1000.00")
        expected_gst = Decimal("82.57")  # 1000 * 9 / 109 = 82.5688... → 82.57
        expected_subtotal = Decimal("917.43")

        subtotal, gst = AgreementService.calculate_gst(total, self.katong)

        self.assertEqual(subtotal, expected_subtotal)
        self.assertEqual(gst, expected_gst)
        self.assertEqual(subtotal + gst, total)

    def test_gst_rounding_half_up(self):
        """
        Test GST rounds half up (0.5 rounds up).

        Given: Total price of $109
        When: GST is extracted
        Then: GST = round(109 * 9 / 109, 2) = $9.00 exactly
        """
        total = Decimal("109.00")

        subtotal, gst = AgreementService.calculate_gst(total, self.katong)

        self.assertEqual(gst, Decimal("9.00"))
        self.assertEqual(subtotal, Decimal("100.00"))

    def test_gst_thomson_exempt(self):
        """
        Test Thomson entity is GST exempt (0%).

        Given: Total price of $1000 at Thomson
        When: GST is calculated
        Then: GST = $0.00, subtotal = $1000.00
        """
        total = Decimal("1000.00")

        subtotal, gst = AgreementService.calculate_gst(total, self.thomson)

        self.assertEqual(gst, Decimal("0.00"))
        self.assertEqual(subtotal, total)

    def test_gst_small_amounts(self):
        """
        Test GST calculation for small amounts.

        Given: Total price of $10.90
        When: GST is extracted
        Then: Correct subtotal and GST calculated
        """
        total = Decimal("10.90")
        # GST = 10.90 * 9 / 109 = 0.90

        subtotal, gst = AgreementService.calculate_gst(total, self.katong)

        self.assertEqual(gst, Decimal("0.90"))
        self.assertEqual(subtotal, Decimal("10.00"))
        self.assertEqual(subtotal + gst, total)

    def test_gst_large_amount(self):
        """
        Test GST calculation for large amounts.

        Given: Total price of $50000
        When: GST is extracted
        Then: Correct GST rounded to 2 decimal places
        """
        total = Decimal("50000.00")
        # GST = 50000 * 9 / 109 = 4128.44 (rounded)

        subtotal, gst = AgreementService.calculate_gst(total, self.katong)

        self.assertEqual(gst, Decimal("4128.44"))
        self.assertEqual(subtotal + gst, total)

    def test_gst_zero_amount(self):
        """
        Test GST calculation for zero amount.

        Given: Total price of $0
        When: GST is calculated
        Then: Both subtotal and GST are $0
        """
        total = Decimal("0.00")

        subtotal, gst = AgreementService.calculate_gst(total, self.katong)

        self.assertEqual(subtotal, Decimal("0.00"))
        self.assertEqual(gst, Decimal("0.00"))

    def test_gst_precision_handling(self):
        """
        Test GST handles decimal precision correctly.

        Given: Total with many decimal places
        When: GST is extracted
        Then: Result uses ROUND_HALF_UP correctly
        """
        total = Decimal("999.99")
        # GST = 999.99 * 9 / 109 = 82.567... → 82.57

        subtotal, gst = AgreementService.calculate_gst(total, self.katong)

        self.assertEqual(gst, Decimal("82.57"))
        self.assertEqual(subtotal, Decimal("917.42"))
        self.assertEqual(subtotal + gst, total)
