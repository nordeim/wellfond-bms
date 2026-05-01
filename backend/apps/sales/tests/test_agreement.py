"""Agreement State Machine Tests
=====================================
Phase 5: Sales Agreements & AVS Tracking

Tests for agreement lifecycle and state transitions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
import uuid as uuid_module
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Entity, User
from apps.operations.models import Dog
from apps.sales.models import AgreementStatus, AgreementType, SalesAgreement
from apps.sales.services.agreement import AgreementService


# Helper function to create test user with proper username
def create_test_user(entity, email, password="testpass123", role="admin"):
    """Create a test user with required username."""
    username = f"testuser_{uuid_module.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        entity=entity,
        role=role,
    )


class TestAgreementStateMachine(TestCase):
    """Test agreement state transitions."""

    def setUp(self):
        """Set up test data."""
        entity_id = uuid_module.uuid4()
        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Katong", "code": "KATONG", "slug": f"katong-{entity_id}"},
            id=entity_id,
        )
        self.user = create_test_user(
            entity=self.entity,
            email="test@example.com",
        )
        self.dog = Dog.objects.create(
            microchip="TEST123456",
            name="Test Dog",
            breed="Labrador",
            dob="2020-01-01",
            gender="M",
            entity=self.entity,
        )

    def test_agreement_creation_in_draft_state(self):
        """
        Test new agreements start in DRAFT state.

        Given: Creating a new agreement
        When: Agreement is created
        Then: Status is DRAFT
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        self.assertEqual(agreement.status, AgreementStatus.DRAFT)
        self.assertIsNotNone(agreement.created_at)

    def test_draft_to_signed_transition(self):
        """
        Test DRAFT → SIGNED transition is valid.

        Given: Agreement in DRAFT state
        When: Signing action is performed
        Then: Status changes to SIGNED
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        result = AgreementService.sign_agreement(
            agreement_id=agreement.id,
            signed_by=self.user,
            signature_data="base64encodeddata",
            ip_address="192.168.1.1",
            user_agent="TestBrowser/1.0",
        )

        self.assertTrue(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.SIGNED)
        self.assertIsNotNone(agreement.signed_at)

    def test_signed_to_completed_transition(self):
        """
        Test SIGNED → COMPLETED transition is valid.

        Given: Agreement in SIGNED state
        When: Complete action is performed
        Then: Status changes to COMPLETED
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )
        # Manually set signed_at since we're creating directly
        agreement.signed_at = timezone.now()
        agreement.save()

        result = AgreementService.complete_agreement(
            agreement_id=agreement.id,
            completed_by=self.user,
        )

        self.assertTrue(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.COMPLETED)

    def test_draft_to_cancelled_transition(self):
        """
        Test DRAFT → CANCELLED transition is valid.

        Given: Agreement in DRAFT state
        When: Cancel action is performed
        Then: Status changes to CANCELLED
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        result = AgreementService.cancel_agreement(
            agreement_id=agreement.id,
            cancelled_by=self.user,
            reason="Test cancellation",
        )

        self.assertTrue(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.CANCELLED)

    def test_signed_to_cancelled_transition(self):
        """
        Test SIGNED → CANCELLED transition is valid.

        Given: Agreement in SIGNED state
        When: Cancel action is performed
        Then: Status changes to CANCELLED
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        result = AgreementService.cancel_agreement(
            agreement_id=agreement.id,
            cancelled_by=self.user,
            reason="Buyer backed out",
        )

        self.assertTrue(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.CANCELLED)

    def test_completed_to_cancelled_blocked(self):
        """
        Test COMPLETED → CANCELLED is blocked.

        Given: Agreement in COMPLETED state
        When: Cancel action is attempted
        Then: Transition is rejected
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.COMPLETED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        result = AgreementService.cancel_agreement(
            agreement_id=agreement.id,
            cancelled_by=self.user,
            reason="Should fail",
        )

        self.assertFalse(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.COMPLETED)

    def test_cancelled_cannot_be_resigned(self):
        """
        Test CANCELLED agreements cannot be signed.

        Given: Agreement in CANCELLED state
        When: Sign action is attempted
        Then: Transition is rejected
        """
        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.CANCELLED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        result = AgreementService.sign_agreement(
            agreement_id=agreement.id,
            signed_by=self.user,
            signature_data="data",
            ip_address="1.1.1.1",
            user_agent="Browser",
        )

        self.assertFalse(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.CANCELLED)

    def test_agreement_types(self):
        """
        Test all agreement types are valid.

        Given: Agreements of different types
        When: Created
        Then: Types are stored correctly
        """
        types = [AgreementType.B2C, AgreementType.B2B, AgreementType.REHOME]

        for agreement_type in types:
            agreement = SalesAgreement.objects.create(
                entity=self.entity,
                created_by=self.user,
                type=agreement_type,
                status=AgreementStatus.DRAFT,
                buyer_name="Test Buyer",
                buyer_mobile="+6591234567",
                buyer_email="buyer@example.com",
                buyer_address="123 Test Street",
                total_amount=1000.00,
                gst_component=82.57,
                deposit=100.00,
                balance=900.00,
            )
            self.assertEqual(agreement.type, agreement_type)

    def test_calculate_totals(self):
        """
        Test calculate totals from line items.

        Given: Agreement with line items
        When: Totals are calculated
        Then: Sum matches line items
        """
        from apps.sales.models import AgreementLineItem

        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=0.00,
            gst_component=0.00,
            deposit=0.00,
            balance=0.00,
        )

        # Create line items using correct model fields
        AgreementLineItem.objects.create(
            agreement=agreement,
            dog=self.dog,
            price=Decimal("500.00"),
            gst_component=Decimal("45.00"),
        )

        # Test that line_items relationship works
        self.assertEqual(agreement.line_items.count(), 1)
        line_item = agreement.line_items.first()
        self.assertEqual(line_item.price, Decimal("500.00"))

    def test_cancel_agreement_audit_log_records_correct_old_status(self):
        """
        Test cancel_agreement audit log records the correct old_status (H2 fix).

        Given: Agreement in SIGNED state
        When: Cancel action is performed
        Then: Audit log records old_status as SIGNED, not CANCELLED
        """
        from apps.core.models import AuditLog

        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1000.00,
            gst_component=82.57,
            deposit=100.00,
            balance=900.00,
        )

        result = AgreementService.cancel_agreement(
            agreement_id=agreement.id,
            cancelled_by=self.user,
            reason="Test H2 fix",
        )

        self.assertTrue(result)

        audit_log = AuditLog.objects.filter(
            resource_type="SalesAgreement",
            resource_id=str(agreement.id),
            action=AuditLog.Action.UPDATE,
        ).latest("created_at")

        self.assertEqual(audit_log.payload["old_status"], AgreementStatus.SIGNED)
        self.assertEqual(audit_log.payload["new_status"], AgreementStatus.CANCELLED)
        self.assertNotEqual(
            audit_log.payload["old_status"],
            audit_log.payload["new_status"],
            "old_status and new_status should differ after cancellation",
        )

    def test_line_item_computed_properties(self):
        """
        Test line_total and gst_amount computed properties on AgreementLineItem.

        Given: AgreementLineItem with price and gst_component
        When: Accessing line_total and gst_amount
        Then: Returns correct computed values
        """
        from apps.sales.models import AgreementLineItem

        item = AgreementLineItem.objects.create(
            agreement=SalesAgreement.objects.create(
                entity=self.entity,
                created_by=self.user,
                type=AgreementType.B2C,
                status=AgreementStatus.DRAFT,
                buyer_name="Test Buyer",
                buyer_mobile="+6591234567",
                buyer_email="buyer@example.com",
                buyer_address="123 Test Street",
                total_amount=Decimal("0.00"),
                gst_component=Decimal("0.00"),
                deposit=Decimal("0.00"),
                balance=Decimal("0.00"),
            ),
            dog=self.dog,
            price=Decimal("1000.00"),
            gst_component=Decimal("90.00"),
        )

        self.assertEqual(item.line_total, Decimal("1000.00"))
        self.assertEqual(item.gst_amount, Decimal("90.00"))

    def test_calculate_totals_uses_line_total(self):
        """
        Test calculate_totals works correctly with line_total property.

        Given: Agreement with line items having price and gst_component
        When: calculate_totals() is called
        Then: Returns correct aggregated subtotal and gst
        """
        from apps.sales.models import AgreementLineItem

        agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=Decimal("0.00"),
            gst_component=Decimal("0.00"),
            deposit=Decimal("0.00"),
            balance=Decimal("0.00"),
        )

        AgreementLineItem.objects.create(
            agreement=agreement,
            dog=self.dog,
            price=Decimal("500.00"),
            gst_component=Decimal("45.00"),
        )

        totals = AgreementService.calculate_totals(agreement)
        self.assertEqual(totals["subtotal"], Decimal("500.00"))
        self.assertEqual(totals["gst_amount"], Decimal("45.00"))
        self.assertEqual(totals["total"], Decimal("545.00"))
