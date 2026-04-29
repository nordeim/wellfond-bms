"""
GST report tests.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.core.models import Entity
from apps.finance.services.gst_report import extract_gst, validate_gst_calculation


class TestGSTCalculation(TestCase):
    """Test GST extraction formula."""

    def test_gst_sums_components(self):
        """Test GST extraction for standard prices."""
        # Formula: GST = price * 9 / 109, ROUND_HALF_UP
        assert extract_gst(Decimal("109.00")) == Decimal("9.00")
        assert extract_gst(Decimal("218.00")) == Decimal("18.00")

    def test_gst_rounding(self):
        """Test GST rounding behavior."""
        # 50 * 9 / 109 = 4.128... → rounds to 4.13
        assert extract_gst(Decimal("50.00")) == Decimal("4.13")

    def test_gst_thomson_zero(self):
        """Test Thomson entity has 0 GST."""
        assert extract_gst(Decimal("109.00"), "THOMSON") == Decimal("0.00")
        assert extract_gst(Decimal("500.00"), "thomson") == Decimal("0.00")

    def test_gst_standard_entities(self):
        """Test standard entities have GST applied."""
        assert extract_gst(Decimal("109.00"), "HOLDINGS") == Decimal("9.00")
        assert extract_gst(Decimal("109.00"), "KATONG") == Decimal("9.00")


class TestGSTValidation(TestCase):
    """Test GST validation."""

    def test_validate_calculation(self):
        """Test GST calculation validation."""
        assert validate_gst_calculation(Decimal("109.00"), Decimal("9.00"))
        assert validate_gst_calculation(Decimal("218.00"), Decimal("18.00"))
        assert validate_gst_calculation(Decimal("50.00"), Decimal("4.13"))

    def test_validate_fails_on_wrong_amount(self):
        """Test validation fails on incorrect GST."""
        assert not validate_gst_calculation(Decimal("109.00"), Decimal("8.00"))
