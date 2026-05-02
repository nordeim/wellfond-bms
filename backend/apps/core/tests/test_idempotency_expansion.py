"""
Test: Idempotency Required for All Write Operations
Critical Issue C3: Idempotency only enforced on log paths

These tests ensure all state-changing operations require idempotency keys.
"""

import uuid

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


class IdempotencyNonJsonClearTests(TestCase):
    """RED phase: non-JSON 2xx responses must clear the processing marker.

    BUG: When a 2xx response body is non-JSON (e.g. StreamingHttpResponse,
    plain text, SSE), the inner try/except at middleware.py catches
    json.JSONDecodeError and silently passes.  The processing marker remains
    in Redis (set at line 84 with 30s TTL), and the successful response is
    never cached for replay.  Subsequent retries re-process instead.
    """

    def setUp(self):
        self.factory = RequestFactory()
        from django.http import StreamingHttpResponse

        def _inner(_request):
            return StreamingHttpResponse(
                iter(["data: ok\n\n"]),
                content_type="text/event-stream",
                status=200,
            )

        self.middleware = IdempotencyMiddleware(_inner)

    def test_non_json_2xx_does_not_leave_processing_marker(self):
        """GREEN: non-JSON 2xx must NOT leave a stale processing marker.

        We verify by sending a second request with the SAME idempotency key.
        Before fix: second request re-processes (no cached replay available).
        After fix: processing marker is cleared, second request goes through
        cleanly without hitting the 409 conflict from the stale marker.
        """
        from django.core.cache import caches

        idempotency_key = "test-key-sse-01"

        # First request — non-JSON SSE response
        request1 = self.factory.post(
            "/api/v1/operations/logs/in-heat",
            content_type="application/json",
            data={"dog_id": "123"},
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )
        response1 = self.middleware(request1)
        self.assertEqual(response1.status_code, 200)

        # Second request — same key.
        # Before fix: the processing marker was left behind (30s TTL).
        #   The middleware sees a cached entry with status="processing" and
        #   returns 409 Conflict.
        # After fix: the processing marker is cleared, so the second request
        #   acquires the lock fresh and proceeds normally.
        request2 = self.factory.post(
            "/api/v1/operations/logs/in-heat",
            content_type="application/json",
            data={"dog_id": "123"},
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )
        response2 = self.middleware(request2)

        self.assertNotEqual(
            response2.status_code, 409,
            "Second request got 409 Conflict — processing marker from first "
            "non-JSON response was not cleared. The middleware must delete "
            "the processing marker when a 2xx response is non-JSON.",
        )
