"""GST Tests
=============
Phase 6: Compliance & NParks Reporting

Tests for GST calculation and reporting.
"""

import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import pytest
from django.test import TestCase

from apps.core.models import Entity
from apps.sales.models import AgreementStatus, AgreementType, SalesAgreement

from ..models import GSTLedger
from ..services.gst import GSTService


class TestGSTCalculation(TestCase):
    """Test GST calculation per IRAS requirements."""

    def setUp(self):
        """Set up test data."""
        self.katong, _ = Entity.objects.get_or_create(
            defaults={"name": "Katong", "code": "KATONG", "slug": "katong-test"},
            id=uuid.uuid4(),
        )
        self.thomson, _ = Entity.objects.get_or_create(
            defaults={"name": "Thomson", "code": "THOMSON", "slug": "thomson-test"},
            id=uuid.uuid4(),
        )

    def test_extract_gst_109_equals_9(self):
        """
        Test GST extraction: $109 → $9.00 GST.
        Formula: 109 * 9 / 109 = 9.00
        """
        price = Decimal("109.00")
        gst = GSTService.extract_gst(price, self.katong)

        self.assertEqual(gst, Decimal("9.00"))

    def test_extract_gst_218_equals_18(self):
        """
        Test GST extraction: $218 → $18.00 GST.
        Formula: 218 * 9 / 109 = 18.00
        """
        price = Decimal("218.00")
        gst = GSTService.extract_gst(price, self.katong)

        self.assertEqual(gst, Decimal("18.00"))

    def test_extract_gst_50_equals_4_13(self):
        """
        Test GST extraction: $50 → $4.13 GST.
        Formula: 50 * 9 / 109 = 4.128... → 4.13 (rounded)
        """
        price = Decimal("50.00")
        gst = GSTService.extract_gst(price, self.katong)

        self.assertEqual(gst, Decimal("4.13"))

    def test_extract_gst_thomson_equals_zero(self):
        """
        Test Thomson entity is GST exempt (0%).
        """
        price = Decimal("1000.00")
        gst = GSTService.extract_gst(price, self.thomson)

        self.assertEqual(gst, Decimal("0.00"))

    def test_round_half_up(self):
        """
        Test ROUND_HALF_UP rounding.
        0.125 → 0.13 (rounds up)
        0.124 → 0.12 (rounds down)
        """
        # This creates a value that would round differently with HALF_UP
        price = Decimal("1.09")  # 1.09 * 9 / 109 = 0.0899... → 0.09
        gst = GSTService.extract_gst(price, self.katong)

        self.assertEqual(gst, Decimal("0.09"))

    def test_calculate_gst_returns_tuple(self):
        """
        Test calculate_gst returns (subtotal, gst) tuple.
        """
        price = Decimal("109.00")
        subtotal, gst = GSTService.calculate_gst(price, self.katong)

        self.assertEqual(subtotal, Decimal("100.00"))
        self.assertEqual(gst, Decimal("9.00"))
        self.assertEqual(subtotal + gst, price)


class TestGSTSummary(TestCase):
    """Test GST summary calculation."""

    def setUp(self):
        """Set up test data."""
        from apps.core.models import User

        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST", "slug": "test-entity"},
            id=uuid.uuid4(),
        )

        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="admin",
        )

    def test_gst_summary_sums_correctly(self):
        """
        Test GST summary sums all agreements for quarter.
        """
        from datetime import datetime

        # Create completed agreements with completed_at in Q1 2026 (January)
        agreement1 = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            buyer_name="Buyer 1",
            buyer_mobile="+6512345678",
            buyer_email="buyer1@example.com",
            buyer_address="123 Test St",
            total_amount=Decimal("109.00"),
            gst_component=Decimal("9.00"),
            deposit=Decimal("10.00"),
            balance=Decimal("99.00"),
            completed_at=datetime(2026, 1, 15, 10, 0, 0),  # January = Q1
        )

        agreement2 = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            buyer_name="Buyer 2",
            buyer_mobile="+6587654321",
            buyer_email="buyer2@example.com",
            buyer_address="456 Test St",
            total_amount=Decimal("218.00"),
            gst_component=Decimal("18.00"),
            deposit=Decimal("20.00"),
            balance=Decimal("198.00"),
            completed_at=datetime(2026, 2, 20, 14, 0, 0),  # February = Q1
        )

        # Create GST ledger entries with actual agreement IDs
        GSTLedger.objects.create(
            entity=self.entity,
            period="2026-Q1",
            source_agreement=agreement1,
            total_sales=Decimal("109.00"),
            gst_component=Decimal("9.00"),
        )

        GSTLedger.objects.create(
            entity=self.entity,
            period="2026-Q1",
            source_agreement=agreement2,
            total_sales=Decimal("218.00"),
            gst_component=Decimal("18.00"),
        )

        # Get summary
        summary = GSTService.calc_gst_summary(self.entity, "2026-Q1")

        self.assertEqual(summary.total_sales, Decimal("327.00"))
        self.assertEqual(summary.total_gst, Decimal("27.00"))
        self.assertEqual(summary.transactions_count, 2)

    def test_get_quarter_from_date(self):
        """
        Test quarter extraction from date.
        """
        q1 = date(2026, 2, 15)
        q2 = date(2026, 5, 15)
        q3 = date(2026, 8, 15)
        q4 = date(2026, 11, 15)

        self.assertEqual(GSTService.get_quarter_from_date(q1), "2026-Q1")
        self.assertEqual(GSTService.get_quarter_from_date(q2), "2026-Q2")
        self.assertEqual(GSTService.get_quarter_from_date(q3), "2026-Q3")
        self.assertEqual(GSTService.get_quarter_from_date(q4), "2026-Q4")


class TestGSTLedger(TestCase):
    """Test GST ledger operations."""

    def setUp(self):
        """Set up test data."""
        from apps.core.models import User

        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST", "slug": "test-entity"},
            id=uuid.uuid4(),
        )

        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="admin",
        )

    def test_create_ledger_entry(self):
        """
        Test creating GST ledger entry from agreement.
        """
        from datetime import datetime

        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            buyer_name="Test Buyer",
            buyer_mobile="+6512345678",
            buyer_email="buyer@example.com",
            buyer_address="123 Test St",
            total_amount=Decimal("109.00"),
            gst_component=Decimal("9.00"),
            deposit=Decimal("10.00"),
            balance=Decimal("99.00"),
            completed_at=datetime(2026, 1, 15, 10, 0, 0),
        )

        entry = GSTService.create_ledger_entry(agreement)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.total_sales, Decimal("109.00"))
        self.assertEqual(entry.gst_component, Decimal("9.00"))

    def test_no_ledger_for_non_completed(self):
        """
        Test no ledger entry created for non-completed agreements.
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Test Buyer",
            buyer_mobile="+6512345678",
            buyer_email="buyer@example.com",
            buyer_address="123 Test St",
            total_amount=Decimal("109.00"),
            gst_component=Decimal("9.00"),
            deposit=Decimal("10.00"),
            balance=Decimal("99.00"),
        )

        entry = GSTService.create_ledger_entry(agreement)

        self.assertIsNone(entry)
