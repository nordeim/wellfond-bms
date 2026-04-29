"""
Test: Idempotency Cache Isolation
High Issue H1: Session and idempotency share Redis cache

These tests ensure idempotency uses a dedicated Redis instance.
"""

from django.test import TestCase, override_settings
from django.conf import settings


class IdempotencyCacheIsolationTests(TestCase):
    """Tests for HIGH-1: Isolate idempotency cache to dedicated Redis."""

    def test_idempotency_cache_uses_dedicated_redis(self):
        """
        Test: Idempotency cache should use REDIS_IDEMPOTENCY_URL,
        not REDIS_CACHE_URL.
        """
        idempotency_cache = settings.CACHES.get("idempotency", {})
        location = idempotency_cache.get("LOCATION", "")

        # Should be configured via REDIS_IDEMPOTENCY_URL env var
        # which defaults to redis_idempotency host or dedicated DB
        import os
        expected_from_env = os.environ.get("REDIS_IDEMPOTENCY_URL", "redis://redis_idempotency:6379/0")

        # Either matches env var or contains idempotency-specific host/DB
        is_dedicated = (
            "idempotency" in location.lower() or  # Dedicated host
            location != settings.CACHES.get("default", {}).get("LOCATION", "") or  # Different from default
            location != settings.CACHES.get("sessions", {}).get("LOCATION", "")  # Different from sessions
        )

        self.assertTrue(
            is_dedicated,
            f"Idempotency cache should use dedicated Redis (host='idempotency' or different DB), "
            f"but got: {location}. Expected from env: {expected_from_env}"
        )

        # Should NOT use the same URL as default cache
        default_location = settings.CACHES.get("default", {}).get("LOCATION", "")
        self.assertNotEqual(
            location,
            default_location,
            "Idempotency cache should NOT share URL with default cache"
        )

        # Should NOT use the same URL as sessions
        sessions_location = settings.CACHES.get("sessions", {}).get("LOCATION", "")
        self.assertNotEqual(
            location,
            sessions_location,
            "Idempotency cache should NOT share URL with sessions cache"
        )

    def test_idempotency_cache_backend_is_redis(self):
        """Test: Idempotency cache uses Redis backend."""
        idempotency_cache = settings.CACHES.get("idempotency", {})

        self.assertEqual(
            idempotency_cache.get("BACKEND"),
            "django.core.cache.backends.redis.RedisCache",
            "Idempotency cache should use RedisCache backend"
        )

    def test_all_caches_have_unique_locations(self):
        """Test: All cache locations should be unique."""
        locations = []
        for cache_name, config in settings.CACHES.items():
            location = config.get("LOCATION", "")
            if location:
                self.assertNotIn(
                    location,
                    locations,
                    f"Cache '{cache_name}' shares location with another cache: {location}"
                )
                locations.append(location)
