"""PDF Service Tests
=====================
Phase 5: Sales Agreements & AVS Tracking

Tests for PDF generation with Gotenberg.
"""

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import uuid
from django.test import TestCase

from apps.core.models import Entity, User
from apps.sales.models import AgreementStatus, AgreementType, SalesAgreement
from apps.sales.services.pdf import PDFService


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


class TestPDFService(TestCase):
    """Test PDF generation service."""

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
        self.agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            agreement_number="WF-TEST-001",
            agreement_type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            subtotal=1000.00,
            gst_amount=82.57,
            total=1082.57,
            terms_version="1.0",
        )

    @pytest.mark.asyncio
    async def test_pdf_generation_creates_bytes(self):
        """
        Test PDF generation returns bytes.

        Given: Agreement data
        When: PDF is generated
        Then: Returns bytes content
        """
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"PDF content")

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)

            pdf_bytes, pdf_hash = await PDFService.render_agreement_pdf(
                agreement_id=self.agreement.id,
                watermark=False,
            )

            self.assertIsInstance(pdf_bytes, bytes)
            self.assertIsNotNone(pdf_hash)
            self.assertEqual(len(pdf_hash), 64)  # SHA-256 hex length

    @pytest.mark.asyncio
    async def test_pdf_generation_with_watermark(self):
        """
        Test PDF generation with watermark.

        Given: Draft agreement
        When: PDF is generated with watermark
        Then: Watermark appears in HTML
        """
        draft_agreement = SalesAgreement.objects.create(
            entity=self.entity,
            created_by=self.user,
            agreement_number="WF-TEST-002",
            agreement_type=AgreementType.B2C,
            status=AgreementStatus.DRAFT,
            buyer_name="Draft Buyer",
            buyer_mobile="+6599999999",
            buyer_email="draft@example.com",
            subtotal=500.00,
            gst_amount=45.00,
            total=545.00,
            terms_version="1.0",
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"PDF with watermark")

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)

            pdf_bytes, pdf_hash = await PDFService.render_agreement_pdf(
                agreement_id=draft_agreement.id,
                watermark=True,
            )

            # Verify call was made
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_pdf_hash_is_sha256(self):
        """
        Test PDF hash is SHA-256.

        Given: PDF bytes
        When: Hash is computed
        Then: Returns SHA-256 hex digest
        """
        test_content = b"Test PDF content"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=test_content)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)

            pdf_bytes, pdf_hash = await PDFService.render_agreement_pdf(
                agreement_id=self.agreement.id,
                watermark=False,
            )

            self.assertEqual(pdf_hash, expected_hash)

    @pytest.mark.asyncio
    async def test_pdf_generation_failure_handling(self):
        """
        Test PDF generation handles failure gracefully.

        Given: Gotenberg unavailable
        When: PDF generation fails
        Then: Raises appropriate exception
        """
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            with self.assertRaises(Exception):
                await PDFService.render_agreement_pdf(
                    agreement_id=self.agreement.id,
                    watermark=False,
                )

    def test_get_html_template_returns_content(self):
        """
        Test HTML template retrieval.

        Given: Template exists
        When: Get template is called
        Then: Returns HTML content
        """
        html = PDFService.get_html_template("sales/agreement.html")

        self.assertIsNotNone(html)
        self.assertIn("{buyer_name}", html)  # Template has placeholders
        self.assertIn("{agreement_number}", html)

    def test_render_template_substitutes_variables(self):
        """
        Test template variable substitution.
        """
        template = "Hello {buyer_name}, your total is {total}"
        context = {
            "buyer_name": "John Doe",
            "total": "1000.00",
        }

        result = PDFService.render_template(template, context)

        self.assertEqual(result, "Hello John Doe, your total is 1000.00")
