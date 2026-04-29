"""
Test: Idempotency Required for All Write Operations
Critical Issue C3: Idempotency only enforced on log paths

These tests ensure all state-changing operations require idempotency keys.
"""

from django.test import TestCase, RequestFactory
from django.http import JsonResponse

from ..middleware import IdempotencyMiddleware


class IdempotencyExpansionTests(TestCase):
    """Tests for CRITICAL-3: Expand idempotency enforcement."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = IdempotencyMiddleware(lambda r: JsonResponse({"status": "ok"}))

    def test_post_to_breeding_requires_idempotency(self):
        """POST to breeding endpoints should require idempotency key."""
        request = self.factory.post(
            "/api/v1/breeding/litters",
            content_type="application/json",
            data={"name": "Test Litter"}
        )
        response = self.middleware(request)

        # Should return 400 requiring idempotency key
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"idempotency", response.content.lower())

    def test_post_to_sales_requires_idempotency(self):
        """POST to sales endpoints should require idempotency key."""
        request = self.factory.post(
            "/api/v1/sales/agreements",
            content_type="application/json",
            data={"customer_id": "123"}
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"idempotency", response.content.lower())

    def test_post_to_finance_requires_idempotency(self):
        """POST to finance endpoints should require idempotency key."""
        request = self.factory.post(
            "/api/v1/finance/transactions",
            content_type="application/json",
            data={"amount": 100}
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"idempotency", response.content.lower())

    def test_post_to_customers_requires_idempotency(self):
        """POST to customers endpoints should require idempotency key."""
        request = self.factory.post(
            "/api/v1/customers/",
            content_type="application/json",
            data={"name": "Test Customer"}
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"idempotency", response.content.lower())

    def test_put_requires_idempotency(self):
        """PUT requests should require idempotency key."""
        request = self.factory.put(
            "/api/v1/dogs/123",
            content_type="application/json",
            data={"name": "Updated"}
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)

    def test_patch_requires_idempotency(self):
        """PATCH requests should require idempotency key."""
        request = self.factory.patch(
            "/api/v1/dogs/123",
            content_type="application/json",
            data={"status": "active"}
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)

    def test_delete_requires_idempotency(self):
        """DELETE requests should require idempotency key."""
        request = self.factory.delete("/api/v1/dogs/123")
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)

    def test_auth_endpoints_exempt(self):
        """Auth endpoints should NOT require idempotency."""
        request = self.factory.post(
            "/api/v1/auth/login",
            content_type="application/json",
            data={"email": "test@test.com", "password": "password"}
        )
        response = self.middleware(request)

        # Should pass through (not require idempotency)
        self.assertEqual(response.status_code, 200)

    def test_get_requests_exempt(self):
        """GET requests should NOT require idempotency."""
        request = self.factory.get("/api/v1/dogs/")
        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_operations_logs_still_requires_idempotency(self):
        """Operations logs should still require idempotency."""
        request = self.factory.post(
            "/api/v1/operations/logs/in-heat",
            content_type="application/json",
            data={"dog_id": "123"}
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"idempotency", response.content.lower())
