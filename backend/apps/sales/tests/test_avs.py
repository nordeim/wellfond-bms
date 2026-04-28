"""AVS Service Tests
=====================
Phase 5: Sales Agreements & AVS Tracking

Tests for AVS token generation, reminders, and completion.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
import uuid
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Entity, User
from apps.operations.models import Dog
from apps.sales.models import AVSStatus, AgreementStatus, AgreementType
from apps.sales.services.avs import AVSService


# Helper function to create test user with proper username
def create_test_user(entity, email, password="testpass123", role="admin"):
    """Create a test user with required username."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        entity=entity,
        role=role,
    )


class TestAVSService(TestCase):
    """Test AVS service functionality."""

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
            microchip="AVS123456789",
            name="Test Dog",
            breed="Labrador",
            dob="2020-01-01",
            gender="M",
            entity=self.entity,
        )
        from apps.sales.models import SalesAgreement
        self.agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            total_amount=1082.57,
            gst_component=82.57,
            deposit=100.00,
            balance=982.57,
        )

    def test_token_generation(self):
        """
        Test AVS token is generated for transfer.

        Given: Agreement and dog
        When: AVS transfer is created
        Then: Token is generated and URL is returned
        """
        transfer = AVSService.create_transfer(
            agreement_id=self.agreement.id,
            dog_id=self.dog.id,
            buyer_mobile="+6591234567",
            entity_id=self.entity.id,
        )

        self.assertIsNotNone(transfer.token)
        self.assertEqual(len(transfer.token), 36)  # UUID length
        self.assertEqual(transfer.status, AVSStatus.PENDING)

    def test_transfer_link_generation(self):
        """
        Test AVS link is properly formatted.

        Given: Transfer with token
        When: Get AVS link is called
        Then: Returns properly formatted URL
        """
        from apps.sales.models import AVSTransfer
        transfer = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591234567",
            token="test-token-123",
            status=AVSStatus.SENT,
        )

        link = AVSService.get_avs_link(transfer.token)

        self.assertIn(transfer.token, link)
        self.assertIn("/avs/", link)

    def test_mark_completed(self):
        """
        Test marking transfer as completed.

        Given: Transfer in SENT state
        When: Mark completed is called
        Then: Status changes to COMPLETED
        """
        from apps.sales.models import AVSTransfer
        transfer = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591234567",
            token="test-token-123",
            status=AVSStatus.SENT,
        )

        result = AVSService.mark_completed(transfer.token)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AVSStatus.COMPLETED)
        self.assertIsNotNone(result.completed_at)

    def test_invalid_token_rejected(self):
        """
        Test invalid token is rejected.

        Given: Invalid token
        When: Mark completed is called
        Then: Returns None (not found)
        """
        result = AVSService.mark_completed("invalid-token")

        self.assertIsNone(result)

    def test_check_pending_reminders(self):
        """
        Test finding transfers needing reminders.

        Given: Transfers older than 72 hours
        When: Check pending reminders is called
        Then: Returns list of pending transfers
        """
        from apps.sales.models import AVSTransfer
        # Create transfer older than 72 hours
        old_transfer = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591234567",
            token="old-token",
            status=AVSStatus.SENT,
        )
        # Manually set created_at to 3 days ago
        old_transfer.created_at = timezone.now() - timedelta(days=3)
        old_transfer.save()

        pending = AVSService.check_pending_reminders()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].id, old_transfer.id)

    def test_escalation_needed(self):
        """
        Test escalation is needed after reminder + 24 hours.

        Given: Transfer with reminder sent 24+ hours ago
        When: Check escalation is called
        Then: Returns True
        """
        from apps.sales.models import AVSTransfer
        transfer = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591234567",
            token="test-token",
            status=AVSStatus.SENT,
        )
        transfer.reminder_sent_at = timezone.now() - timedelta(hours=25)
        transfer.save()

        needs_escalation = AVSService.check_escalation_needed(transfer)

        self.assertTrue(needs_escalation)

    def test_no_escalation_recent_reminder(self):
        """
        Test escalation not needed for recent reminders.

        Given: Transfer with reminder sent 12 hours ago
        When: Check escalation is called
        Then: Returns False
        """
        from apps.sales.models import AVSTransfer
        transfer = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591234567",
            token="test-token",
            status=AVSStatus.SENT,
        )
        transfer.reminder_sent_at = timezone.now() - timedelta(hours=12)
        transfer.save()

        needs_escalation = AVSService.check_escalation_needed(transfer)

        self.assertFalse(needs_escalation)

    def test_escalation_updates_status(self):
        """
        Test escalation updates transfer status.

        Given: Transfer needing escalation
        When: Escalate to staff is called
        Then: Transfer is marked escalated
        """
        from apps.sales.models import AVSTransfer
        transfer = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591234567",
            token="test-token",
            status=AVSStatus.SENT,
        )

        AVSService.escalate_to_staff(transfer)

        transfer.refresh_from_db()
        self.assertEqual(transfer.status, AVSStatus.ESCALATED)

    def test_get_pending_transfers(self):
        """
        Test retrieving pending transfers by entity.

        Given: Multiple transfers across entities
        When: Get pending is called
        Then: Returns only matching entity transfers
        """
        from apps.sales.models import AVSTransfer, SalesAgreement
        # Create transfer for current entity
        transfer1 = AVSTransfer.objects.create(
            agreement=self.agreement,
            dog=self.dog,
            entity=self.entity,
            buyer_mobile="+6591111111",
            token="token-1",
            status=AVSStatus.PENDING,
        )

        # Create transfer for different entity
        other_entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Other", "code": "OTHER"},
            id=uuid.uuid4(),
        )
        other_user = create_test_user(
            entity=other_entity,
            email="other@example.com",
        )
        other_agreement = SalesAgreement.objects.create(
            entity=other_entity,
            created_by=other_user,
            agreement_type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Other Buyer",
            buyer_mobile="+6599999999",
            buyer_email="other@example.com",
            subtotal=500.00,
            gst_amount=45.00,
            total=545.00,
            terms_version="1.0",
        )
        other_dog = Dog.objects.create(
            microchip="OTHER123",
            name="Other Dog",
            breed="Poodle",
            dob="2020-01-01",
            gender="F",
            entity=other_entity,
        )
        transfer2 = AVSTransfer.objects.create(
            agreement=other_agreement,
            dog=other_dog,
            entity=other_entity,
            buyer_mobile="+6592222222",
            token="token-2",
            status=AVSStatus.PENDING,
        )

        pending = AVSService.get_pending_transfers(self.entity.id)

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].id, transfer1.id)
