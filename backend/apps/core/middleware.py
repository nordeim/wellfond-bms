"""
Core Middleware - Wellfond BMS
================================
Idempotency middleware for safe retry semantics.
"""

import hashlib
import json
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse


class IdempotencyMiddleware:
    """
    Ensures POST/PUT/PATCH/DELETE requests with same idempotency key
    return cached response for 24 hours.

    Header: X-Idempotency-Key: <uuid>
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return self.get_response(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return self.get_response(request)

        # Generate cache key from request fingerprint
        fingerprint = self._generate_fingerprint(request, idempotency_key)
        cached_response = cache.get(fingerprint)

        if cached_response:
            # Return cached response with Idempotency-Replay header
            response = JsonResponse(
                cached_response["data"], status=cached_response["status"]
            )
            response["Idempotency-Replay"] = "true"
            return response

        # Process request and cache response
        response = self.get_response(request)

        if 200 <= response.status_code < 300:
            cache.set(
                fingerprint,
                {"data": json.loads(response.content), "status": response.status_code},
                timeout=86400,  # 24 hours
            )

        return response

    def _generate_fingerprint(self, request, idempotency_key):
        """Generate unique fingerprint for request."""
        user_id = request.user.id if request.user.is_authenticated else "anon"
        path = request.path
        body = request.body.decode() if request.body else ""

        data = f"{user_id}:{path}:{body}:{idempotency_key}"
        return f"idempotency:{hashlib.sha256(data.encode()).hexdigest()}"
