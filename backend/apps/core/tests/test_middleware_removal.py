"""
Test: Verify only one AuthenticationMiddleware is registered.
Critical Issue C2: Duplicate AuthenticationMiddleware conflict.

This test ensures the fix is correctly applied.
"""

from django.test import TestCase, override_settings
from django.conf import settings


class MiddlewareRemovalTests(TestCase):
    """Tests for CRITICAL-2: Remove duplicate AuthenticationMiddleware."""

    def test_single_authentication_middleware(self):
        """
        Test: Only one AuthenticationMiddleware should be registered.

        The custom apps.core.middleware.AuthenticationMiddleware should be present,
        but django.contrib.auth.middleware.AuthenticationMiddleware should NOT be.
        """
        middleware_list = settings.MIDDLEWARE

        # Count AuthenticationMiddleware occurrences
        custom_middleware = "apps.core.middleware.AuthenticationMiddleware"
        django_middleware = "django.contrib.auth.middleware.AuthenticationMiddleware"

        custom_count = middleware_list.count(custom_middleware)
        django_count = middleware_list.count(django_middleware)

        # Should have exactly 1 custom middleware
        self.assertEqual(
            custom_count, 1,
            f"Expected 1 custom AuthenticationMiddleware, found {custom_count}"
        )

        # Should have 0 Django middleware (removed per fix)
        self.assertEqual(
            django_count, 0,
            f"Expected 0 Django AuthenticationMiddleware (should be removed), found {django_count}. "
            f"This causes race conditions where request.user may be overwritten."
        )

    def test_middleware_order(self):
        """
        Test: Custom AuthenticationMiddleware must run AFTER CsrfViewMiddleware.

        This ensures CSRF validation happens before user authentication.
        """
        middleware_list = settings.MIDDLEWARE

        csrf_idx = middleware_list.index("django.middleware.csrf.CsrfViewMiddleware")
        custom_idx = middleware_list.index("apps.core.middleware.AuthenticationMiddleware")

        self.assertGreater(
            custom_idx, csrf_idx,
            "AuthenticationMiddleware must run AFTER CsrfViewMiddleware"
        )

    def test_django_contrib_auth_still_in_installed_apps(self):
        """
        Test: Django auth should still be in INSTALLED_APPS for admin support.

        The middleware is removed, but the app should remain for ModelBackend.
        """
        self.assertIn(
            "django.contrib.auth",
            settings.INSTALLED_APPS,
            "django.contrib.auth must remain in INSTALLED_APPS for admin compatibility"
        )

    def test_idempotency_middleware_order(self):
        """
        Test: IdempotencyMiddleware must run AFTER AuthenticationMiddleware.

        This ensures request.user is available when generating fingerprints.
        """
        middleware_list = settings.MIDDLEWARE

        auth_idx = middleware_list.index("apps.core.middleware.AuthenticationMiddleware")
        idem_idx = middleware_list.index("apps.core.middleware.IdempotencyMiddleware")

        self.assertGreater(
            idem_idx, auth_idx,
            "IdempotencyMiddleware must run AFTER AuthenticationMiddleware "
            "to access request.user for fingerprinting"
        )
