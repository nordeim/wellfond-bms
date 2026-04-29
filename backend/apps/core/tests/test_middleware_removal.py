"""
Test: Verify AuthenticationMiddleware configuration.
Updated: Django admin requires django.contrib.auth.middleware.AuthenticationMiddleware.

Both middlewares are needed:
- Custom: Sets request.user from Redis sessions for API
- Django: Required for Django admin to function
"""

from django.test import TestCase, override_settings
from django.conf import settings


class MiddlewareRemovalTests(TestCase):
    """Tests for AuthenticationMiddleware configuration."""

    def test_both_authentication_middlewares_present(self):
        """
        Test: Both AuthenticationMiddlewares should be registered.

        - Custom: Sets request.user from Redis sessions for API auth
        - Django: Required for Django admin functionality (admin.E408)
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

        # Should have 1 Django middleware (required for admin)
        self.assertEqual(
            django_count, 1,
            f"Expected 1 Django AuthenticationMiddleware (required for admin), found {django_count}"
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
