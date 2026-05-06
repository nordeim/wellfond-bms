"""
Tests for IdempotencyMiddleware non-JSON response handling.
Critical Issue C-007: Non-JSON responses break exactly-once semantics.
"""
import hashlib
from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.test import TestCase, RequestFactory
from django.core.cache import caches

from apps.core.middleware import IdempotencyMiddleware


class TestIdempotencyNonJsonHandling(TestCase):
    """
    Test that non-JSON responses are handled correctly.
    C-007: Middleware should not cache non-JSON responses.
    """

    def setUp(self):
        """Set up test."""
        self.factory = RequestFactory()

    def _get_fingerprint(self, request, idempotency_key):
        """Calculate fingerprint the same way middleware does."""
        session_id = request.COOKIES.get("sessionid", "anon")
        path = request.path
        body = request.body.decode() if request.body else ""
        data = f"{session_id}:{path}:{body}:{idempotency_key}"
        return f"idempotency:{hashlib.sha256(data.encode()).hexdigest()}"

    @patch('apps.core.middleware.caches')
    def test_non_json_success_keeps_processing_marker(self, mock_caches):
        """Test that successful non-JSON responses keep processing marker."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache

        request = self.factory.post('/api/v1/test/')
        request.META['HTTP_X_IDEMPOTENCY_KEY'] = 'test-key-123'
        request.COOKIES = {'sessionid': 'test-session'}
        request._body = b''

        mock_cache.get.return_value = {"status": "processing"}

        def get_response(request):
            response = HttpResponse(b'PDF content', content_type='application/pdf')
            response.status_code = 200
            return response

        middleware = IdempotencyMiddleware(get_response=get_response)
        result = middleware(request)

        mock_cache.delete.assert_not_called()

    @patch('apps.core.middleware.caches')
    def test_json_response_is_cached(self, mock_caches):
        """Test that JSON responses are cached correctly."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache
        mock_cache.get.return_value = None  # No cached response

        request = self.factory.post('/api/v1/test/')
        request.META['HTTP_X_IDEMPOTENCY_KEY'] = 'test-key-456'
        request.COOKIES = {'sessionid': 'test-session'}
        request._body = b''

        def get_response(request):
            return JsonResponse({"status": "success"}, status=200)

        middleware = IdempotencyMiddleware(get_response=get_response)
        result = middleware(request)

        self.assertEqual(result.status_code, 200)
        mock_cache.set.assert_called()

    @patch('apps.core.middleware.caches')
    def test_non_json_error_deletes_marker(self, mock_caches):
        """Test that non-JSON error responses DELETE processing marker (so retries work)."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache

        request = self.factory.post('/api/v1/test/')
        request.META['HTTP_X_IDEMPOTENCY_KEY'] = 'test-key-789'
        request.COOKIES = {'sessionid': 'test-session'}
        request._body = b''

        mock_cache.get.return_value = {"status": "processing"}

        def get_response(request):
            response = HttpResponse(b'Error', content_type='text/plain', status=500)
            response.status_code = 500
            return response

        middleware = IdempotencyMiddleware(get_response=get_response)
        result = middleware(request)

        mock_cache.delete.assert_called()
