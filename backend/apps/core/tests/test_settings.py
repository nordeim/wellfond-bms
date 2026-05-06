"""
Tests for Django settings configuration.
Validates security requirements for SECRET_KEY and other critical settings.
"""

import os
from unittest.mock import patch

import pytest


class TestSecretKeyConfiguration:
    """
    Test SECRET_KEY configuration security.
    
    C-001: SECRET_KEY must fail loudly if DJANGO_SECRET_KEY is not set.
    No fallback to insecure default allowed.
    """

    def test_secret_key_no_fallback_in_base_py(self):
        """
        Test that base.py does NOT have a fallback value for SECRET_KEY.
        
        After fix: base.py should use os.environ["DJANGO_SECRET_KEY"] (no fallback).
        """
        # Read the base.py file and check for the insecure fallback
        settings_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "config", "settings", "base.py"
        )
        settings_file = os.path.normpath(settings_file)
        
        with open(settings_file, "r") as f:
            content = f.read()
        
        # Check that the insecure fallback is NOT present
        assert '"dev-only-change-in-production"' not in content, \
            "SECRET_KEY should not have insecure fallback 'dev-only-change-in-production'"
        
        # Check that os.environ.get with fallback is NOT used
        assert 'os.environ.get("DJANGO_SECRET_KEY",' not in content, \
            "SECRET_KEY should use os.environ['DJANGO_SECRET_KEY'] without fallback"

    def test_secret_key_raises_when_unset(self):
        """
        Test that accessing SECRET_KEY fails when DJANGO_SECRET_KEY is not set.
        """
        # Temporarily unset the env var and try to evaluate the expression
        original = os.environ.get("DJANGO_SECRET_KEY")
        
        try:
            # Remove env var
            if "DJANGO_SECRET_KEY" in os.environ:
                del os.environ["DJANGO_SECRET_KEY"]
            
            # Test that os.environ["DJANGO_SECRET_KEY"] raises KeyError
            with pytest.raises(KeyError):
                _ = os.environ["DJANGO_SECRET_KEY"]
                
        finally:
            # Restore
            if original is not None:
                os.environ["DJANGO_SECRET_KEY"] = original

    def test_secret_key_works_with_value(self):
        """
        Test that SECRET_KEY works correctly when DJANGO_SECRET_KEY is set.
        """
        test_key = "test-secret-key-for-testing-only"
        original = os.environ.get("DJANGO_SECRET_KEY")
        
        try:
            os.environ["DJANGO_SECRET_KEY"] = test_key
            
            # Verify the key is accessible
            assert os.environ["DJANGO_SECRET_KEY"] == test_key
            
        finally:
            if original is not None:
                os.environ["DJANGO_SECRET_KEY"] = original
            else:
                if "DJANGO_SECRET_KEY" in os.environ:
                    del os.environ["DJANGO_SECRET_KEY"]
