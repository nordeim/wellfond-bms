"""Test SESSION-002: SESSION_COOKIE_SECURE must be set in base.py.

FIX-02: SESSION_COOKIE_SECURE is currently only set in production.py.
Django defaults to False, so non-production environments send cookies
over HTTP without Secure flag. Fix: add to base.py as `not DEBUG`.
"""

import pytest
from django.test import TestCase


class TestSessionCookieSecure(TestCase):
    """Verify SESSION_COOKIE_SECURE is defined in base settings."""

    def test_session_cookie_secure_exists_in_base(self):
        """SESSION_COOKIE_SECURE must be present in base.py settings."""
        from config.settings.base import DEBUG, SESSION_COOKIE_SECURE
        # Should be True in production (DEBUG=False), False in dev (DEBUG=True)
        assert SESSION_COOKIE_SECURE == (not DEBUG)
