"""GST Calculation Fix Tests

Tests for validating that GST extraction uses entity.gst_rate field
instead of hardcoded entity name.

TDD Phase 1: Write failing test before implementation.
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP

from apps.core.models import Entity
from apps.sales.services.agreement import AgreementService


@pytest.mark.django_db
class TestGSTCalculation:
    """Test GST calculation uses gst_rate field, not hardcoded entity name."""

    def test_extract_gst_uses_gst_rate_field_not_hardcoded_name(self):
        """
        Test that GST extraction uses entity.gst_rate, not hardcoded name.
        
        This test creates an entity with 0% GST but a non-"Thomson" name
        and verifies that GST is correctly calculated as 0.00.
        """
        # Create entity with 0% GST but different name (not "Thomson")
        entity = Entity.objects.create(
            name="Zero Tax Entity",
            code="ZERO_GST",
            gst_rate=Decimal("0.00")  # 0% GST
        )
        
        price = Decimal("109.00")
        gst = AgreementService.extract_gst(price, entity)
        
        # Should return 0.00 because gst_rate=0, not because of hardcoded name
        assert gst == Decimal("0.00"), (
            f"Expected 0.00 GST for entity with gst_rate=0.00, "
            f"but got {gst}. The code is likely using hardcoded entity name "
            f"instead of gst_rate field."
        )

    def test_extract_gst_for_standard_9_percent_entity(self):
        """Test normal 9% GST calculation."""
        entity = Entity.objects.create(
            name="Holdings",
            code="HOLDINGS",
            gst_rate=Decimal("0.09")
        )
        
        price = Decimal("109.00")
        gst = AgreementService.extract_gst(price, entity)
        
        # GST = 109 * 9 / 109 = 9.00
        expected = Decimal("9.00")
        assert gst == expected, (
            f"Expected {expected} GST for 9% rate on {price}, but got {gst}"
        )

    def test_extract_gst_rounding_half_up(self):
        """Test GST rounding uses ROUND_HALF_UP."""
        entity = Entity.objects.create(
            name="Test Entity",
            code="TEST",
            gst_rate=Decimal("0.09")
        )
        
        # Price that will produce fractional cents
        price = Decimal("50.00")
        gst = AgreementService.extract_gst(price, entity)
        
        # GST = 50 * 9 / 109 = 4.1284... → should round to 4.13
        expected = Decimal("4.13")
        assert gst == expected, (
            f"Expected {expected} GST (rounded HALF_UP), but got {gst}"
        )

    def test_thomson_entity_still_works_with_gst_rate(self):
        """Verify Thomson entity works when using gst_rate-based approach."""
        # Create Thomson entity with 0% gst_rate (as it should be in DB)
        entity = Entity.objects.create(
            name="Thomson",
            code="THOMSON",
            gst_rate=Decimal("0.00")
        )
        
        price = Decimal("1000.00")
        gst = AgreementService.extract_gst(price, entity)
        
        assert gst == Decimal("0.00"), (
            f"Thomson entity should return 0 GST when gst_rate=0"
        )

    def test_multiple_gst_rates(self):
        """Test that different GST rates work correctly."""
        # Test 7% rate (hypothetical future rate)
        entity_7 = Entity.objects.create(
            name="Seven Percent",
            code="SEVEN",
            gst_rate=Decimal("0.07")
        )
        
        price = Decimal("107.00")
        gst = AgreementService.extract_gst(price, entity_7)
        
        # GST = 107 * 7 / 107 = 7.00
        assert gst == Decimal("7.00"), (
            f"7% GST rate should calculate correctly"
        )
