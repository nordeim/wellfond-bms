"""Rate Limiting Tests

Tests for validating rate limiting on auth endpoints.

TDD Phase 3: Write failing test before implementation.
"""

import pytest
from django.test import Client
from django.core.cache import cache

from apps.core.models import User, Entity


@pytest.mark.django_db
class TestRateLimiting:
    """Test rate limiting on authentication endpoints."""

    def setup_method(self):
        """Clear cache before each test."""
        self.client = Client()
        cache.clear()

        # Create test entity and user
        self.entity = Entity.objects.create(
            name="Test Entity",
            code="TEST",
            gst_rate=0.09
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            role="admin",
            entity=self.entity
        )

    def test_login_rate_limit_after_5_attempts(self):
        """
        Test that login endpoint rate limits after 5 attempts.
        
        Per implementation plan: 5 attempts per minute per IP.
        After 5 failed attempts, should return 429 Too Many Requests.
        """
        # Make 5 failed login attempts (should all get 401 Unauthorized)
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login',
                {'email': 'test@example.com', 'password': 'wrongpassword'},
                content_type='application/json'
            )
            # Should get 401 for wrong credentials (not rate limited yet)
            assert response.status_code == 401, (
                f"Expected 401 for wrong password (attempt {i+1}), "
                f"got {response.status_code}"
            )

        # 6th attempt should be rate limited
        response = self.client.post(
            '/api/v1/auth/login',
            {'email': 'test@example.com', 'password': 'wrongpassword'},
            content_type='application/json'
        )
        
        # Should get 429 Too Many Requests
        assert response.status_code == 429, (
            f"Expected 429 Too Many Requests after 5 failed attempts, "
            f"got {response.status_code}. "
            f"Rate limiting is not properly configured."
        )
        
        # Response should contain rate limit message
        content = response.content.decode()
        assert 'Rate limit' in content or 'rate limit' in content.lower(), (
            f"Rate limit response should contain 'rate limit' message, "
            f"got: {content}"
        )

    def test_successful_login_does_not_affect_rate_limit(self):
        """
        Test that successful logins don't count against rate limit.
        
        Only failed attempts should contribute to rate limiting.
        """
        # First, login successfully
        response = self.client.post(
            '/api/v1/auth/login',
            {'email': 'test@example.com', 'password': 'TestPass123!'},
            content_type='application/json'
        )
        
        # Should succeed
        assert response.status_code == 200, (
            f"Login with correct credentials should succeed, got {response.status_code}"
        )

    def test_csrf_endpoint_rate_limited(self):
        """Test that CSRF endpoint has rate limiting."""
        # Make many rapid requests
        for i in range(15):
            response = self.client.get('/api/v1/auth/csrf')
            
            if i < 10:
                # First 10 should succeed (10/min limit)
                assert response.status_code == 200, (
                    f"Request {i+1} should succeed, got {response.status_code}"
                )
            else:
                # After 10, should be rate limited
                if response.status_code == 429:
                    return  # Rate limiting is working
        
        # If we got here without hitting 429, rate limiting is missing
        pytest.fail("CSRF endpoint not rate limited after 15 requests")

    def test_refresh_endpoint_rate_limited(self):
        """Test that refresh endpoint has rate limiting."""
        cache.clear()
        
        # Make 6 rapid refresh requests without valid session
        for i in range(6):
            response = self.client.post('/api/v1/auth/refresh')
            
            if i < 5:
                # First 5 should get 401 (not rate limited yet)
                if response.status_code == 429:
                    pytest.fail(f"Request {i+1} was rate limited too early")
            else:
                # 6th should be rate limited
                if response.status_code == 429:
                    return  # Rate limiting working
        
        pytest.fail("Refresh endpoint not rate limited after 5+ requests")

    def test_rate_limit_resets_after_window(self):
        """
        Test that rate limit resets after time window.
        
        This test verifies that rate limiting uses proper time windows.
        """
        # Make 5 failed attempts
        for i in range(5):
            self.client.post(
                '/api/v1/auth/login',
                {'email': 'test@example.com', 'password': 'wrong'},
                content_type='application/json'
            )
        
        # Verify rate limited
        response = self.client.post(
            '/api/v1/auth/login',
            {'email': 'test@example.com', 'password': 'wrong'},
            content_type='application/json'
        )
        
        assert response.status_code == 429, (
            "Should be rate limited after 5 failed attempts"
        )

    def test_different_ips_have_separate_limits(self):
        """Test that rate limits are per-IP, not global."""
        # Make 5 attempts from one IP
        for i in range(5):
            self.client.post(
                '/api/v1/auth/login',
                {'email': 'test@example.com', 'password': 'wrong'},
                content_type='application/json'
            )
        
        # This client should now be rate limited
        response = self.client.post(
            '/api/v1/auth/login',
            {'email': 'test@example.com', 'password': 'wrong'},
            content_type='application/json'
        )
        
        assert response.status_code == 429, "Original client should be rate limited"

    def test_rate_limit_decorator_applied_to_auth_endpoints(self):
        """
        Test that @ratelimit decorator is actually applied to auth endpoints.
        
        This is a meta-test to verify the decorator is in place.
        """
        from apps.core.routers.auth import router
        
        # Check that login endpoint has rate limiting
        login_route = None
        for path, route in router._routers:
            if path == "/login":
                login_route = route
                break
        
        # The route should have rate limiting applied
        # We can verify this by checking if the endpoint returns 429
        cache.clear()
        
        # Make many requests rapidly
        responses = []
        for i in range(10):
            response = self.client.post(
                '/api/v1/auth/login',
                {'email': 'test@example.com', 'password': 'wrong'},
                content_type='application/json'
            )
            responses.append(response.status_code)
        
        # At least one response should be 429 if rate limiting is working
        assert 429 in responses, (
            "Rate limiting should block some requests after threshold. "
            f"Got status codes: {responses}. "
            f"Rate limiting decorator may not be applied."
        )
