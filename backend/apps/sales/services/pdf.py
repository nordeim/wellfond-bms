"""PDF Service — Phase 5: Sales Agreements & AVS Tracking.

Renders agreements as PDFs using Gotenberg (Chromium-based) for pixel-perfect
legal documents with e-signature fidelity.
"""

import hashlib
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

import httpx
from django.conf import settings
from django.template.loader import render_to_string

from apps.core.models import User

from ..models import SalesAgreement

logger = logging.getLogger(__name__)

# Gotenberg configuration
GOTENBERG_URL = getattr(settings, "GOTENBERG_URL", "http://localhost:3000")
GOTENBERG_TIMEOUT = 30.0  # seconds


class PDFService:
    """Service for rendering agreement PDFs via Gotenberg."""

    @staticmethod
    def compute_hash(pdf_bytes: bytes) -> str:
        """
        Compute SHA-256 hash of PDF for integrity verification.

        Args:
            pdf_bytes: Raw PDF bytes

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(pdf_bytes).hexdigest()

    @staticmethod
    def render_html_template(agreement: SalesAgreement) -> str:
        """
        Render agreement data to HTML template.

        Args:
            agreement: SalesAgreement instance

        Returns:
            HTML string
        """
        from ..services.agreement import AgreementService

        # Get T&C content
        tc_content = AgreementService.get_tc_content(agreement.type)

        # Get line items with dog details
        line_items = []
        for item in agreement.line_items.select_related("dog").all():
            line_items.append({
                "microchip": item.dog.microchip,
                "name": item.dog.name,
                "breed": item.dog.breed,
                "gender": item.dog.gender,
                "dob": item.dog.dob,
                "price": item.price,
                "gst": item.gst_component,
            })

        # Get signatures
        signatures = []
        for sig in agreement.signatures.all():
            signatures.append({
                "signer_type": sig.signer_type,
                "method": sig.method,
                "timestamp": sig.timestamp,
                "image_url": sig.image_url,
            })

        context = {
            "agreement": {
                "id": str(agreement.id),
                "type": agreement.type,
                "status": agreement.status,
                "created_at": agreement.created_at,
            },
            "buyer": {
                "name": agreement.buyer_name,
                "nric": agreement.buyer_nric,
                "mobile": agreement.buyer_mobile,
                "email": agreement.buyer_email,
                "address": agreement.buyer_address,
                "housing_type": agreement.buyer_housing_type,
            },
            "pricing": {
                "total": agreement.total_amount,
                "gst": agreement.gst_component,
                "deposit": agreement.deposit,
                "balance": agreement.balance,
                "payment_method": agreement.payment_method,
            },
            "line_items": line_items,
            "special_conditions": agreement.special_conditions,
            "tc_content": tc_content,
            "signatures": signatures,
            "is_draft": agreement.status == "DRAFT",
        }

        # Render template
        return render_to_string("sales/agreement.html", context)

    @staticmethod
    async def render_agreement_pdf(
        agreement_id: UUID,
        watermark: bool = False,
    ) -> tuple[bytes, str]:
        """
        Render agreement as PDF using Gotenberg.

        Args:
            agreement_id: Agreement UUID
            watermark: Whether to add "DRAFT" watermark

        Returns:
            Tuple of (pdf_bytes, sha256_hash)

        Raises:
            RuntimeError: If PDF generation fails
        """
        try:
            agreement = await SalesAgreement.objects.select_related(
                "entity", "created_by"
            ).prefetch_related(
                "line_items__dog", "signatures"
            ).aget(id=agreement_id)
        except SalesAgreement.DoesNotExist:
            raise RuntimeError(f"Agreement not found: {agreement_id}")

        # Render HTML
        html_content = PDFService.render_html_template(agreement)

        # Add watermark for drafts
        if watermark or agreement.status == "DRAFT":
            html_content = PDFService._add_watermark(html_content, "DRAFT")

        # Check if Gotenberg is available
        if not PDFService._is_gotenberg_available():
            logger.warning("Gotenberg not available, using mock PDF (HTML)")
            return PDFService._mock_pdf(html_content)

        try:
            async with httpx.AsyncClient(timeout=GOTENBERG_TIMEOUT) as client:
                response = await client.post(
                    f"{GOTENBERG_URL}/forms/chromium/convert/html",
                    data={
                        "paperWidth": "8.27",  # A4
                        "paperHeight": "11.69",
                        "marginTop": "0.4",
                        "marginBottom": "0.4",
                        "marginLeft": "0.4",
                        "marginRight": "0.4",
                    },
                    files={
                        "index.html": ("index.html", html_content, "text/html"),
                    },
                )
                response.raise_for_status()

                pdf_bytes = response.content
                pdf_hash = PDFService.compute_hash(pdf_bytes)

                logger.info(f"PDF generated for agreement {agreement_id}: {pdf_hash}")

                return pdf_bytes, pdf_hash

        except httpx.RequestError as e:
            logger.error(f"Gotenberg request failed: {e}")
            raise RuntimeError(f"PDF generation failed: {e}")

    @staticmethod
    def _is_gotenberg_available() -> bool:
        """Check if Gotenberg service is available."""
        import httpx

        try:
            response = httpx.get(f"{GOTENBERG_URL}/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _mock_pdf(html_content: str) -> tuple[bytes, str]:
        """
        Create mock PDF (HTML saved as PDF) for dev/testing.

        In development, saves HTML and returns placeholder PDF bytes.
        """
        # Save HTML to file for inspection
        html_bytes = html_content.encode("utf-8")
        pdf_hash = PDFService.compute_hash(html_bytes)

        logger.info(f"Mock PDF generated (HTML): {pdf_hash}")

        return html_bytes, pdf_hash

    @staticmethod
    def _add_watermark(html_content: str, text: str) -> str:
        """Add watermark to HTML content."""
        watermark_css = f"""
        <style>
            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 100px;
                color: rgba(200, 200, 200, 0.3);
                z-index: 1000;
                pointer-events: none;
            }}
        </style>
        <div class="watermark">{text}</div>
        """

        # Insert before closing </body> or at end
        if "</body>" in html_content:
            return html_content.replace("</body>", f"{watermark_css}</body>")
        return html_content + watermark_css

    @staticmethod
    def verify_hash(pdf_bytes: bytes, expected_hash: str) -> bool:
        """
        Verify PDF integrity by comparing SHA-256 hash.

        Args:
            pdf_bytes: PDF bytes to verify
            expected_hash: Expected SHA-256 hash

        Returns:
            True if hash matches
        """
        computed = PDFService.compute_hash(pdf_bytes)
        return computed == expected_hash

    @staticmethod
    def render_agreement_pdf_sync(
        agreement_id: UUID,
        watermark: bool = False,
    ) -> tuple[bytes, str]:
        """
        Synchronous wrapper for render_agreement_pdf.

        Use this in synchronous contexts like tests or Celery tasks.
        The async version should be used in async contexts like FastAPI/Ninja endpoints.

        Uses sync_to_async bridge to properly handle Django ORM in async context.

        Args:
            agreement_id: Agreement UUID
            watermark: Whether to add "DRAFT" watermark

        Returns:
            Tuple of (pdf_bytes, sha256_hash)
        """
        from asgiref.sync import async_to_sync

        return async_to_sync(PDFService.render_agreement_pdf)(agreement_id, watermark)
