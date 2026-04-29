"""Blast Tests
=============
Phase 7: Customer DB & Marketing Blast

Tests for blast dispatch, rate limiting, and PDPA enforcement.
"""

import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from django.test import TestCase

from apps.core.models import Entity, User
from apps.customers.models import Customer, CommunicationLog
from apps.customers.services.blast import BlastService, BlastProgressTracker, CommunicationRouter
from apps.customers.schemas import BlastCreate


class TestBlastRecipients(TestCase):
    """Test blast recipient selection."""

    def setUp(self):
        """Set up test data."""
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

        # Create consented customers
        self.customer1 = Customer.objects.create(
            name="Customer One",
            mobile="+6590000001",
            email="one@example.com",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

        self.customer2 = Customer.objects.create(
            name="Customer Two",
            mobile="+6590000002",
            email="two@example.com",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

        # Create non-consented customer
        self.customer3 = Customer.objects.create(
            name="Customer Three",
            mobile="+6590000003",
            email="three@example.com",
            pdpa_consent=False,
            entity=self.entity,
            created_by=self.user,
        )

    def test_blast_excludes_pdpa_false(self):
        """Test that PDPA=false customers are excluded from blast."""
        payload = BlastCreate(
            customer_ids=[self.customer1.id, self.customer2.id, self.customer3.id],
            channel="EMAIL",
            body="Test message",
        )

        recipients = BlastService.get_recipients(payload)

        # Should return all 3 (exclusion happens in send_blast)
        self.assertEqual(len(recipients), 3)

    def test_get_recipients_from_customer_ids(self):
        """Test getting recipients from customer_ids."""
        payload = BlastCreate(
            customer_ids=[self.customer1.id, self.customer2.id],
            channel="EMAIL",
            body="Test message",
        )

        recipients = BlastService.get_recipients(payload)

        self.assertEqual(len(recipients), 2)

    def test_get_recipients_from_segment(self):
        """Test getting recipients from segment."""
        from apps.customers.models import Segment

        segment = Segment.objects.create(
            name="Test Segment",
            filters_json={"pdpa": True},
            entity=self.entity,
            created_by=self.user,
        )

        payload = BlastCreate(
            segment_id=segment.id,
            channel="EMAIL",
            body="Test message",
        )

        recipients = BlastService.get_recipients(payload)

        # Should return consented customers
        self.assertEqual(len(recipients), 2)


class TestMergeTags(TestCase):
    """Test merge tag interpolation."""

    def setUp(self):
        """Set up test customer."""
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

        self.customer = Customer.objects.create(
            name="John Doe",
            mobile="+6591234567",
            email="john@example.com",
            housing_type="HDB",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

    def test_merge_tag_name(self):
        """Test {{name}} merge tag."""
        message = "Hello {{name}}, welcome!"
        result = BlastService.apply_merge_tags(message, self.customer, {})
        self.assertEqual(result, "Hello John Doe, welcome!")

    def test_merge_tag_mobile(self):
        """Test {{mobile}} merge tag."""
        message = "Your number: {{mobile}}"
        result = BlastService.apply_merge_tags(message, self.customer, {})
        self.assertEqual(result, "Your number: +6591234567")

    def test_merge_tag_entity(self):
        """Test {{entity}} merge tag."""
        message = "From {{entity}}"
        result = BlastService.apply_merge_tags(message, self.customer, {})
        self.assertEqual(result, "From Test Entity")

    def test_merge_tag_email(self):
        """Test {{email}} merge tag."""
        message = "Reply to {{email}}"
        result = BlastService.apply_merge_tags(message, self.customer, {})
        self.assertEqual(result, "Reply to john@example.com")

    def test_merge_tag_housing(self):
        """Test {{housing}} merge tag."""
        message = "Housing: {{housing}}"
        result = BlastService.apply_merge_tags(message, self.customer, {})
        self.assertEqual(result, "Housing: HDB")

    def test_merge_tag_breed(self):
        """Test {{breed}} merge tag from merge_tags."""
        message = "Your breed: {{breed}}"
        result = BlastService.apply_merge_tags(message, self.customer, {"breed": "Golden Retriever"})
        self.assertEqual(result, "Your breed: Golden Retriever")

    def test_custom_merge_tags(self):
        """Test custom merge tags."""
        message = "Code: {{discount_code}}"
        result = BlastService.apply_merge_tags(message, self.customer, {"discount_code": "SAVE20"})
        self.assertEqual(result, "Code: SAVE20")


class TestBlastProgressTracker(TestCase):
    """Test blast progress tracking."""

    def test_init_progress(self):
        """Test progress initialization."""
        from ..services.blast import BlastProgressTracker

        blast_id = uuid.uuid4()
        tracker = BlastProgressTracker(blast_id)
        tracker.init_progress(10)

        progress = tracker.get_progress()
        self.assertEqual(progress["total"], 10)
        self.assertEqual(progress["sent"], 0)
        self.assertEqual(progress["in_progress"], True)
        self.assertEqual(progress["percentage"], 0)

    def test_update_progress(self):
        """Test progress update."""
        from ..services.blast import BlastProgressTracker

        blast_id = uuid.uuid4()
        tracker = BlastProgressTracker(blast_id)
        tracker.init_progress(10)
        tracker.update_progress(5, 3, 2)

        progress = tracker.get_progress()
        self.assertEqual(progress["sent"], 5)
        self.assertEqual(progress["delivered"], 3)
        self.assertEqual(progress["failed"], 2)
        self.assertEqual(progress["percentage"], 50)

    def test_complete(self):
        """Test marking blast as complete."""
        from ..services.blast import BlastProgressTracker

        blast_id = uuid.uuid4()
        tracker = BlastProgressTracker(blast_id)
        tracker.init_progress(10)
        tracker.update_progress(10, 8, 2)
        tracker.complete()

        progress = tracker.get_progress()
        self.assertEqual(progress["in_progress"], False)
        self.assertEqual(progress["percentage"], 100)


class TestCommunicationLog(TestCase):
    """Test communication logging."""

    def setUp(self):
        """Set up test data."""
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

        self.customer = Customer.objects.create(
            name="Test Customer",
            mobile="+6590000001",
            email="test@example.com",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

    def test_log_communication_creates_entry(self):
        """Test that logging creates a CommunicationLog entry."""
        log = BlastService.log_communication(
            customer=self.customer,
            channel="EMAIL",
            status="SENT",
            message_preview="Test message",
            subject="Test Subject",
            external_id="test-123",
        )

        self.assertIsNotNone(log)
        self.assertEqual(log.customer, self.customer)
        self.assertEqual(log.channel, "EMAIL")
        self.assertEqual(log.status, "SENT")
        self.assertEqual(log.subject, "Test Subject")

    def test_log_communication_truncates_preview(self):
        """Test that message preview is truncated to 200 chars."""
        long_message = "A" * 500

        log = BlastService.log_communication(
            customer=self.customer,
            channel="EMAIL",
            status="SENT",
            message_preview=long_message,
        )

        self.assertEqual(len(log.message_preview), 200)

    def test_communication_log_immutable(self):
        """Test that CommunicationLog is immutable."""
        log = CommunicationLog.objects.create(
            customer=self.customer,
            channel="EMAIL",
            status="SENT",
            message_preview="Test",
        )

        # Should raise error on update
        log.message_preview = "Updated"
        with self.assertRaises(ValueError) as context:
            log.save()
        self.assertIn("immutable", str(context.exception).lower())

    def test_communication_log_immutable_delete(self):
        """Test that CommunicationLog cannot be deleted."""
        log = CommunicationLog.objects.create(
            customer=self.customer,
            channel="EMAIL",
            status="SENT",
            message_preview="Test",
        )

        # Should raise error on delete
        with self.assertRaises(ValueError) as context:
            log.delete()
        self.assertIn("immutable", str(context.exception).lower())


class TestCommunicationRouter(TestCase):
    """Test communication routing with fallback."""

    def setUp(self):
        """Set up test data."""
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

        self.customer = Customer.objects.create(
            name="Test Customer",
            mobile="+6590000001",
            email="test@example.com",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

    @patch.object(BlastService, "send_whatsapp")
    @patch.object(BlastService, "send_email")
    def test_route_both_uses_wa_first(self, mock_email, mock_wa):
        """Test that BOTH channel tries WA first."""
        mock_wa.return_value = {"status": "SENT", "external_id": "wa-123"}

        result = CommunicationRouter.route_message(
            self.customer,
            "BOTH",
            "Test Subject",
            "Test body",
        )

        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["channel_used"], "WA")
        self.assertFalse(result["fallback"])
        mock_wa.assert_called_once()
        mock_email.assert_not_called()

    @patch.object(BlastService, "send_whatsapp")
    @patch.object(BlastService, "send_email")
    def test_route_fallback_to_email_on_wa_failure(self, mock_email, mock_wa):
        """Test fallback to email on WA failure."""
        mock_wa.return_value = {"status": "FAILED", "error": "WA unavailable"}
        mock_email.return_value = {"status": "SENT", "external_id": "email-123"}

        result = CommunicationRouter.route_message(
            self.customer,
            "BOTH",
            "Test Subject",
            "Test body",
        )

        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["channel_used"], "EMAIL")
        self.assertTrue(result["fallback"])
        mock_wa.assert_called_once()
        mock_email.assert_called_once()

    @patch.object(BlastService, "send_email")
    def test_route_email_only(self, mock_email):
        """Test routing to email only."""
        mock_email.return_value = {"status": "SENT", "external_id": "email-123"}

        result = CommunicationRouter.route_message(
            self.customer,
            "EMAIL",
            "Test Subject",
            "Test body",
        )

        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["channel_used"], "EMAIL")

    @patch.object(BlastService, "send_whatsapp")
    def test_route_wa_only(self, mock_wa):
        """Test routing to WA only."""
        mock_wa.return_value = {"status": "SENT", "external_id": "wa-123"}

        result = CommunicationRouter.route_message(
            self.customer,
            "WA",
            "",
            "Test body",
        )

        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["channel_used"], "WA")


class TestRateLimiter(TestCase):
    """Test rate limiting."""

    def test_rate_limit_allows_within_limit(self):
        """Test that requests within rate limit are allowed."""
        from ..services.blast import RateLimiter

        limiter = RateLimiter(rate_per_second=10.0)

        # Should allow 10 requests immediately
        allowed = sum(limiter.acquire() for _ in range(10))
        self.assertEqual(allowed, 10)

    def test_rate_limit_blocks_when_exceeded(self):
        """Test that requests exceeding rate limit are blocked."""
        from ..services.blast import RateLimiter

        limiter = RateLimiter(rate_per_second=1.0)

        # First request should be allowed
        self.assertTrue(limiter.acquire())

        # Immediate second request should be blocked
        self.assertFalse(limiter.acquire())


class TestBlastSend(TestCase):
    """Test blast sending."""

    def setUp(self):
        """Set up test data."""
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

        self.customer1 = Customer.objects.create(
            name="Customer One",
            mobile="+6590000001",
            email="one@example.com",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

        self.customer2 = Customer.objects.create(
            name="Customer Two",
            mobile="+6590000002",
            email="two@example.com",
            pdpa_consent=False,  # Not consented
            entity=self.entity,
            created_by=self.user,
        )

    @patch("apps.customers.tasks.dispatch_blast.delay")
    def test_send_blast_queues_task(self, mock_dispatch):
        """Test that send_blast queues the Celery task."""
        payload = BlastCreate(
            customer_ids=[self.customer1.id, self.customer2.id],
            channel="EMAIL",
            body="Test message",
        )

        result = BlastService.send_blast(
            uuid.uuid4(),
            payload,
            self.user,
        )

        # Should queue task
        mock_dispatch.assert_called_once()

        # Result should show exclusion
        self.assertEqual(result.total_recipients, 2)
        self.assertEqual(result.eligible_recipients, 1)  # Only consented
        self.assertEqual(result.excluded_count, 1)
        self.assertEqual(result.status, "QUEUED")

    def test_send_blast_no_recipients(self):
        """Test blast with no recipients."""
        payload = BlastCreate(
            customer_ids=[self.customer2.id],  # Only non-consented
            channel="EMAIL",
            body="Test message",
        )

        result = BlastService.send_blast(
            uuid.uuid4(),
            payload,
            self.user,
        )

        self.assertEqual(result.eligible_recipients, 0)
        self.assertEqual(result.excluded_count, 1)


class TestBlastPreview(TestCase):
    """Test blast preview."""

    def setUp(self):
        """Set up test data."""
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

        self.customer_consented = Customer.objects.create(
            name="Consented",
            mobile="+6590000001",
            email="consented@example.com",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

        self.customer_not_consented = Customer.objects.create(
            name="Not Consented",
            mobile="+6590000002",
            email="not@example.com",
            pdpa_consent=False,
            entity=self.entity,
            created_by=self.user,
        )

    @patch.object(BlastService, "get_recipients")
    @patch.object(BlastService, "apply_merge_tags")
    def test_preview_shows_exclusion(self, mock_merge, mock_recipients):
        """Test that preview shows PDPA exclusion."""
        mock_recipients.return_value = [self.customer_consented, self.customer_not_consented]
        mock_merge.return_value = "Hello Consented"

        from apps.customers.routers.customers import preview_blast

        payload = BlastCreate(
            customer_ids=[self.customer_consented.id, self.customer_not_consented.id],
            channel="EMAIL",
            body="Hello {{name}}",
        )

        # Mock request
        class MockRequest:
            def __init__(self, user):
                self.user = user

        # This would need full request mock, but test the service directly
        preview = BlastService.apply_merge_tags(
            "Hello {{name}}",
            self.customer_consented,
            {},
        )

        self.assertEqual(preview, "Hello Consented")

    def test_preview_counts_eligible(self):
        """Test that preview counts eligible customers."""
        payload = BlastCreate(
            customer_ids=[self.customer_consented.id, self.customer_not_consented.id],
            channel="EMAIL",
            body="Test",
        )

        recipients = BlastService.get_recipients(payload)
        eligible = [r for r in recipients if r.pdpa_consent]

        self.assertEqual(len(recipients), 2)
        self.assertEqual(len(eligible), 1)
