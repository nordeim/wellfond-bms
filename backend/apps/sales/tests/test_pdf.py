"""PDF Service Tests
=====================
Phase 5: Sales Agreements & AVS Tracking

Tests for PDF generation with Gotenberg.
Uses synchronous wrapper for test compatibility.
"""

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import uuid as uuid_module
from django.test import TestCase

from apps.core.models import Entity, User
from apps.sales.models import AgreementStatus, AgreementType, SalesAgreement
from apps.sales.services.pdf import PDFService


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


class TestPDFService(TestCase):
    """Test PDF generation service."""

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
        self.agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            buyer_address="123 Test Street",
            total_amount=1082.57,
            gst_component=82.57,
            deposit=100.00,
            balance=982.57,
        )

    def test_pdf_generation_creates_bytes(self):
        """
        Test PDF generation returns bytes using sync wrapper.

        Given: Agreement data
        When: PDF is generated via sync wrapper
        Then: Returns bytes content
        """
        # Mock the async HTTP call to avoid actual Gotenberg call
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.content = b"PDF content"

        with patch.object(
            PDFService, "_is_gotenberg_available", return_value=True
        ), patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance

            # Use sync wrapper
            pdf_bytes, pdf_hash = PDFService.render_agreement_pdf_sync(
                agreement_id=self.agreement.id,
                watermark=False,
            )

            self.assertIsInstance(pdf_bytes, bytes)
            self.assertIsNotNone(pdf_hash)
            self.assertEqual(len(pdf_hash), 64)  # SHA-256 hex length

    def test_pdf_hash_is_sha256(self):
        """
        Test PDF hash is SHA-256.

        Given: PDF bytes
        When: Hash is computed
        Then: Returns SHA-256 hex digest
        """
        test_content = b"Test PDF content"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Test the compute_hash method directly
        computed_hash = PDFService.compute_hash(test_content)

        self.assertEqual(computed_hash, expected_hash)

    def test_verify_hash(self):
        """
        Test hash verification.

        Given: PDF bytes and expected hash
        When: Verify hash is called
        Then: Returns True if matches
        """
        test_content = b"Test PDF content"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Correct hash
        self.assertTrue(PDFService.verify_hash(test_content, expected_hash))

        # Incorrect hash
        self.assertFalse(PDFService.verify_hash(test_content, "wrong_hash"))

    def test_mock_pdf_fallback(self):
        """
        Test mock PDF fallback when Gotenberg unavailable.

        Given: Gotenberg is not available
        When: PDF generation is requested
        Then: Returns HTML as mock PDF
        """
        with patch.object(PDFService, "_is_gotenberg_available", return_value=False):
            # Use sync wrapper
            pdf_bytes, pdf_hash = PDFService.render_agreement_pdf_sync(
                agreement_id=self.agreement.id,
                watermark=False,
            )

            self.assertIsInstance(pdf_bytes, bytes)
            self.assertIsNotNone(pdf_hash)
            # Mock PDF returns HTML content
            self.assertIn(b"Test Buyer", pdf_bytes)

    def test_compute_hash(self):
        """
        Test compute_hash method directly.
        """
        test_content = b"Test content"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        result = PDFService.compute_hash(test_content)

        self.assertEqual(result, expected_hash)
        self.assertEqual(len(result), 64)  # SHA-256 hex string length
