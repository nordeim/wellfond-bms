"""Agreement State Machine Tests
=====================================
Phase 5: Sales Agreements & AVS Tracking

Tests for agreement lifecycle and state transitions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
import uuid
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Entity, User
from apps.operations.models import Dog


# Helper function to create test user with proper username
def create_test_user(entity, email, password="testpass123", role="admin"):
    """Create a test user with required username."""
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        entity=entity,
        role=role,
    )
from apps.sales.models import AgreementStatus, AgreementType
from apps.sales.services.agreement import AgreementService

from .factories import AgreementLineItemFactory, SalesAgreementFactory


class TestAgreementStateMachine(TestCase):
    """Test agreement state transitions."""

    def setUp(self):
        """Set up test data."""
        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Katong", "code": "KATONG"},
            id=uuid.uuid4(),
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
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.DRAFT,
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
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.DRAFT,
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
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.SIGNED,
        )

        result = AgreementService.complete_agreement(
            agreement_id=agreement.id,
            completed_by=self.user,
        )

        self.assertTrue(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.COMPLETED)
        self.assertIsNotNone(agreement.completed_at)

    def test_draft_to_cancelled_transition(self):
        """
        Test DRAFT → CANCELLED transition is valid.

        Given: Agreement in DRAFT state
        When: Cancel action is performed
        Then: Status changes to CANCELLED
        """
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.DRAFT,
        )

        result = AgreementService.cancel_agreement(
            agreement_id=agreement.id,
            cancelled_by=self.user,
            reason="Test cancellation",
        )

        self.assertTrue(result)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.CANCELLED)
        self.assertIsNotNone(agreement.cancelled_at)

    def test_signed_to_cancelled_transition(self):
        """
        Test SIGNED → CANCELLED transition is valid.

        Given: Agreement in SIGNED state
        When: Cancel action is performed
        Then: Status changes to CANCELLED
        """
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.SIGNED,
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
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.COMPLETED,
            completed_at=timezone.now(),
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
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            status=AgreementStatus.CANCELLED,
            cancelled_at=timezone.now(),
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
        types = [AgreementType.B2C, AgreementType.B2B, AgreementType.REHOMING]

        for agreement_type in types:
            agreement = SalesAgreementFactory(
                entity=self.entity,
                created_by=self.user,
                agreement_type=agreement_type,
            )
            self.assertEqual(agreement.agreement_type, agreement_type)

    def test_line_items_calculate_totals(self):
        """
        Test line items calculate agreement totals.

        Given: Agreement with line items
        When: Totals are calculated
        Then: Sum matches line items
        """
        agreement = SalesAgreementFactory(
            entity=self.entity,
            created_by=self.user,
            subtotal=Decimal("0.00"),
            gst_amount=Decimal("0.00"),
            total=Decimal("0.00"),
        )

        # Create line items
        item1 = AgreementLineItemFactory(
            agreement=agreement,
            dog=self.dog,
            quantity=1,
            unit_price=Decimal("500.00"),
            line_total=Decimal("500.00"),
            gst_amount=Decimal("45.00"),
        )
        item2 = AgreementLineItemFactory(
            agreement=agreement,
            dog=self.dog,
            quantity=2,
            unit_price=Decimal("250.00"),
            line_total=Decimal("500.00"),
            gst_amount=Decimal("45.00"),
        )

        totals = AgreementService.calculate_totals(agreement)

        expected_subtotal = Decimal("1000.00")
        expected_gst = Decimal("90.00")
        expected_total = Decimal("1090.00")

        self.assertEqual(totals["subtotal"], expected_subtotal)
        self.assertEqual(totals["gst_amount"], expected_gst)
        self.assertEqual(totals["total"], expected_total)
