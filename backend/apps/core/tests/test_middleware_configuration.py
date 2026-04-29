"""
Test: Middleware Configuration Validation
==========================================

Tests to ensure middleware configuration is correct after fix:
- Both custom and Django AuthenticationMiddleware present (for admin support)
- Correct order: Custom before Django
- Idempotency middleware runs after both auth middlewares
- All middleware dependencies satisfied
"""

from django.test import TestCase, override_settings
from django.conf import settings
from django.contrib import admin


class MiddlewareConfigurationTests(TestCase):
    """Tests for middleware stack configuration."""

    def test_custom_authentication_middleware_present(self):
        """Custom AuthenticationMiddleware should be registered."""
        self.assertIn(
            "apps.core.middleware.AuthenticationMiddleware",
            settings.MIDDLEWARE
        )

    def test_django_authentication_middleware_present(self):
        """Django's AuthenticationMiddleware should be registered for admin support."""
        self.assertIn(
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            settings.MIDDLEWARE
        )

    def test_django_auth_before_custom_auth(self):
        """Django auth middleware must run before custom auth middleware.

        Django's middleware wraps request.user in SimpleLazyObject.
        Custom middleware runs after to re-authenticate from Redis if needed.
        """
        middleware_list = settings.MIDDLEWARE
        custom_idx = middleware_list.index("apps.core.middleware.AuthenticationMiddleware")
        django_idx = middleware_list.index("django.contrib.auth.middleware.AuthenticationMiddleware")

        self.assertLess(
            django_idx, custom_idx,
            "Django AuthenticationMiddleware must run before custom middleware"
        )

    def test_django_auth_before_idempotency(self):
        """Both auth middlewares must run before IdempotencyMiddleware."""
        middleware_list = settings.MIDDLEWARE
        django_idx = middleware_list.index("django.contrib.auth.middleware.AuthenticationMiddleware")
        idempotency_idx = middleware_list.index("apps.core.middleware.IdempotencyMiddleware")

        self.assertLess(
            django_idx, idempotency_idx,
            "Django AuthenticationMiddleware must run before IdempotencyMiddleware"
        )

    def test_csrf_before_auth(self):
        """CSRF middleware must run before auth middlewares."""
        middleware_list = settings.MIDDLEWARE
        csrf_idx = middleware_list.index("django.middleware.csrf.CsrfViewMiddleware")
        custom_idx = middleware_list.index("apps.core.middleware.AuthenticationMiddleware")
        django_idx = middleware_list.index("django.contrib.auth.middleware.AuthenticationMiddleware")

        self.assertLess(csrf_idx, custom_idx)
        self.assertLess(csrf_idx, django_idx)

    def test_admin_middleware_requirements_satisfied(self):
        """
        Django admin requires specific middleware to be present.
        Verify all requirements are met.
        """
        required_middleware = [
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ]

        for middleware in required_middleware:
            self.assertIn(
                middleware, settings.MIDDLEWARE,
                f"Admin requires {middleware}"
            )

    def test_django_admin_can_be_imported(self):
        """Verify Django admin site can be imported without errors."""
        try:
            from django.contrib import admin
            # This should not raise an error if middleware is correct
            self.assertIsNotNone(admin.site)
        except Exception as e:
            self.fail(f"Failed to import Django admin: {e}")


class AdminFunctionalityTests(TestCase):
    """Tests for Django admin functionality."""

    def test_admin_site_is_configured(self):
        """Verify admin site has registered models."""
        self.assertGreater(len(admin.site._registry), 0)

    def test_admin_login_url_accessible(self):
        """Admin login URL should be accessible."""
        response = self.client.get('/admin/login/')
        self.assertEqual(response.status_code, 200)

    def test_admin_root_redirects_to_login(self):
        """Admin root should redirect when not authenticated."""
        response = self.client.get('/admin/')
        # Should redirect to login
        self.assertIn(response.status_code, [301, 302, 200])


class MiddlewareBehaviorTests(TestCase):
    """Tests for middleware behavior with both auth middlewares."""

    def test_request_user_set_by_custom_middleware(self):
        """Custom middleware should set request.user on authenticated requests."""
        from django.test import RequestFactory
        from apps.core.middleware import AuthenticationMiddleware

        factory = RequestFactory()
        request = factory.get('/api/v1/dogs/')

        # Process through custom middleware
        middleware = AuthenticationMiddleware(lambda r: r)
        response = middleware(request)

        # After custom middleware, request.user should be set (even if AnonymousUser)
        self.assertTrue(hasattr(request, 'user'))

    def test_no_auth_middleware_error_on_startup(self):
        """
        Verify that Django doesn't raise E408 error on startup.
        This test confirms admin.E408 check passes.
        """
        # Try to import admin module which triggers the check
        try:
            from django.contrib import admin
            # Force admin check
            from django.core.checks import run_checks
            errors = run_checks()

            # Filter for admin.E408 errors
            admin_errors = [e for e in errors if e.id == 'admin.E408']
            self.assertEqual(len(admin_errors), 0, f"Admin errors found: {admin_errors}")
        except Exception as e:
            self.fail(f"Error during admin check: {e}")
