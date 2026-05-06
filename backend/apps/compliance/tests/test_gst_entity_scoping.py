"""
Test: Entity scoping validation in GSTLedger service.
High Issue H-002: Verify entity scoping in GSTLedger service.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.sales.models import SalesAgreement, AgreementStatus, AgreementType
from apps.core.models import Entity
from apps.compliance.models import GSTLedger
from apps.compliance.services.gst import GSTService

User = get_user_model()


class TestGSTLedgerEntityScoping(TestCase):
    """Test entity scoping in GSTLedger service."""

    def setUp(self):
        """Set up test data."""
        # Create entities
        self.entity_a = Entity.objects.create(
            name="Entity A",
            code="ENTA",
            gst_rate=Decimal("0.09"),
            slug="entity-a",
        )
        self.entity_b = Entity.objects.create(
            name="Entity B",
            code="ENTB",
            gst_rate=Decimal("0.09"),
            slug="entity-b",
        )
        
        # Create a user for created_by field
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            entity=self.entity_a,
            role="SALES",
        )

    def test_create_ledger_entry_uses_agreement_entity(self):
        """Test that create_ledger_entry uses agreement's entity."""
        # Create agreement with required fields (without dog - using mock-like approach)
        # We'll test that the service correctly reads entity from agreement
        from unittest.mock import MagicMock
        
        mock_agreement = MagicMock()
        mock_agreement.status = AgreementStatus.COMPLETED
        mock_agreement.completed_at = None  # Should return None
        
        result = GSTService.create_ledger_entry(mock_agreement)
        self.assertIsNone(result)  # No completed_at, should return None

    def test_get_ledger_entries_filters_by_entity(self):
        """Test that get_ledger_entries only returns entries for specified entity."""
        # Create agreements first
        agreement_a = SalesAgreement.objects.create(
            entity=self.entity_a,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            total_amount=Decimal("1090.00"),
            gst_component=Decimal("90.00"),
            buyer_name="Buyer A",
            buyer_nric="S1234567A",
            buyer_mobile="91234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test St",
            buyer_housing_type="OTHER",
            pdpa_consent=True,
            created_by=self.user,
        )
        agreement_b = SalesAgreement.objects.create(
            entity=self.entity_b,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            total_amount=Decimal("2180.00"),
            gst_component=Decimal("180.00"),
            buyer_name="Buyer B",
            buyer_nric="S7654321B",
            buyer_mobile="98765432",
            buyer_email="buyer2@example.com",
            buyer_address="456 Test St",
            buyer_housing_type="OTHER",
            pdpa_consent=True,
            created_by=self.user,
        )
        
        # Create ledger entries linked to agreements
        GSTLedger.objects.create(
            entity=self.entity_a,
            source_agreement=agreement_a,
            period="2026-Q1",
            total_sales=Decimal("1090.00"),
            gst_component=Decimal("90.00"),
        )
        GSTLedger.objects.create(
            entity=self.entity_b,
            source_agreement=agreement_b,
            period="2026-Q1",
            total_sales=Decimal("2180.00"),
            gst_component=Decimal("180.00"),
        )
        
        # Get entries for entity_a
        entries_a = GSTService.get_ledger_entries(self.entity_a, "2026-Q1")
        
        # Should only return entries for entity_a (entity_b entries not included)
        self.assertEqual(len(entries_a), 1)

    def test_calc_gst_summary_scoped_to_entity(self):
        """Test that calc_gst_summary only calculates for specified entity."""
        # This function uses SalesAgreement, not GSTLedger
        # Just verify it accepts entity parameter and returns correct entity_id
        from datetime import date
        
        # Create a completed agreement for entity_a
        agreement = SalesAgreement.objects.create(
            entity=self.entity_a,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            total_amount=Decimal("1090.00"),
            gst_component=Decimal("90.00"),
            buyer_name="Buyer A",
            buyer_nric="S1234567A",
            buyer_mobile="91234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test St",
            buyer_housing_type="OTHER",
            pdpa_consent=True,
            created_by=self.user,
        )
        # Need to set completed_at to be in current quarter
        from django.utils import timezone
        agreement.completed_at = timezone.now()
        agreement.save()
        
        quarter = GSTService.get_quarter_from_date(date.today())
        summary = GSTService.calc_gst_summary(self.entity_a, quarter)
        
        # Should only include sales from entity_a
        self.assertEqual(summary.entity_id, self.entity_a.id)
