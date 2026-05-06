"""
GST Tests
=============
Phase 6: Compliance & NParks Reporting

Tests for GST calculation and reporting.
"""

import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import pytest
from django.test import TestCase

from apps.core.models import Entity, User
from apps.sales.models import SalesAgreement, AgreementStatus, AgreementType
from apps.compliance.models import GSTLedger
from apps.compliance.services.gst import GSTService


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
        from apps.compliance.services.gst import GSTService

        gst = GSTService.extract_gst(
            Decimal("109.00"),
            self.katong,
        )
        self.assertEqual(gst, Decimal("9.00"))

    def test_extract_gst_thomson_zero(self):
        """
        Test GST extraction: Thomson entity = 0% GST.
        Thomson is GST exempt (code = THOMSON).
        """
        from apps.compliance.services.gst import GSTService

        gst = GSTService.extract_gst(
            Decimal("109.00"),
            self.thomson,
        )
        self.assertEqual(gst, Decimal("0.00"))

    def test_calculate_gst_rounding(self):
        """
        Test GST rounding uses ROUND_HALF_UP.
        10.05 * 9 / 109 = 0.83 (not 0.82)
        """
        from apps.compliance.services.gst import GSTService

        gst = GSTService.extract_gst(
            Decimal("10.05"),
            self.katong,
        )
        # 10.05 * 9 / 109 = 0.829... → 0.83 (ROUND_HALF_UP)
        self.assertEqual(gst, Decimal("0.83"))

    def test_create_ledger_entry(self):
        """
        Test creating GST ledger entry via service.
        """
        from apps.sales.models import SalesAgreement, AgreementStatus

        agreement = SalesAgreement.objects.create(
            entity=self.katong,
            type=AgreementType.B2C,
            buyer_name="Test Buyer",
            total_amount=Decimal("109.00"),
            gst_component=Decimal("9.00"),
            status=AgreementStatus.COMPLETED,
            signed_by=self.user,
        )

        entry = GSTService.create_ledger_entry(agreement)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.total_sales, Decimal("109.00"))
        self.assertEqual(entry.gst_component, Decimal("9.00"))

    def test_no_ledger_for_non_completed(self):
        """
        Test no ledger entry created for non-completed agreements.
        """
        from apps.sales.models import SalesAgreement, AgreementStatus

        agreement = SalesAgreement.objects.create(
            entity=self.katong,
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


class TestGSTLedgerImmutability(TestCase):
    """Test that GSTLedger is immutable (H-001 fix)."""

    def setUp(self):
        """Set up test data."""
        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST", "slug": "test-entity"},
            id=uuid.uuid4(),
        )
        self.user = User.objects.create_user(
            username="testuser_gst",
            email="test_gst@example.com",
            password="testpass123",
            entity=self.entity,
        )

    def test_gst_ledger_uses_get_or_create(self):
        """
        Test that GSTLedger uses get_or_create (not update_or_create).
        Should pass after fix because service uses get_or_create.
        """
        from apps.sales.models import SalesAgreement, AgreementStatus

        # Create a sales agreement
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            type=AgreementType.B2C,
            buyer_name="Test Buyer",
            total_amount=Decimal("109.00"),
            gst_component=Decimal("9.00"),
            status=AgreementStatus.COMPLETED,
            signed_by=self.user,
        )

        # Call service to create GST ledger entry
        entry1 = GSTService.create_ledger_entry(agreement)
        self.assertIsNotNone(entry1)

        # Call again with same agreement (should return existing, not update)
        entry2 = GSTService.create_ledger_entry(agreement)
        self.assertIsNotNone(entry2)
        
        # Both should be the same object (get_or_create returns existing)
        self.assertEqual(entry1.id, entry2.id)

    def test_gst_ledger_immutable_update(self):
        """
        Test that GSTLedger cannot be updated.
        Should fail initially because no save() override.
        """
        entry = GSTLedger.objects.create(
            entity=self.entity,
            period="2026-Q1",
            source_agreement=uuid.uuid4(),
            total_sales=Decimal("109.00"),
            gst_component=Decimal("9.00"),
        )

        # Try to update - should raise ValueError after fix
        entry.total_sales = Decimal("218.00")
        with self.assertRaises(ValueError) as context:
            entry.save()
        self.assertIn("immutable", str(context.exception).lower())

    def test_gst_ledger_immutable_delete(self):
        """
        Test that GSTLedger cannot be deleted.
        Should fail initially because no delete() override.
        """
        entry = GSTLedger.objects.create(
            entity=self.entity,
            period="2026-Q2",
            source_agreement=uuid.uuid4(),
            total_sales=Decimal("109.00"),
            gst_component=Decimal("9.00"),
        )

        # Try to delete - should raise ValueError after fix
        with self.assertRaises(ValueError) as context:
            entry.delete()
        self.assertIn("immutable", str(context.exception).lower())
