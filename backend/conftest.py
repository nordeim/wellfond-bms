"""
Shared pytest fixtures for Wellfond BMS.

Provides session-authenticated test client compatible with Django Ninja.
Replaces force_login() which breaks Ninja routers.
"""

import pytest
from django.http import HttpRequest

from apps.core.models import Entity, User


def authenticate_client(client, user):
    """
    Authenticate a Django test client with a session cookie.
    Use this instead of client.force_login() which breaks Ninja routers.

    Args:
        client: Django test Client instance
        user: User model instance

    Usage:
        authenticate_client(client, my_user)
        response = client.get("/api/v1/dogs/")
    """
    from apps.core.auth import SessionManager, AuthenticationService

    req = HttpRequest()
    req.method = "POST"
    req.META["SERVER_NAME"] = "localhost"
    req.META["SERVER_PORT"] = "8000"

    session_key, _ = SessionManager.create_session(user, req)
    client.cookies[AuthenticationService.COOKIE_NAME] = session_key


@pytest.fixture
def test_entity(db):
    """Create a reusable test entity."""
    entity, _ = Entity.objects.get_or_create(
        code=Entity.Code.HOLDINGS,
        defaults={
            "name": "Holdings",
            "slug": "holdings",
            "is_active": True,
            "is_holding": True,
            "gst_rate": 0.09,
        },
    )
    return entity


@pytest.fixture
def test_user(db, test_entity):
    """Create a reusable MANAGEMENT test user."""
    user, _ = User.objects.get_or_create(
        email="testuser@wellfond.sg",
        defaults={
            "username": "testuser",
            "role": User.Role.MANAGEMENT,
            "entity": test_entity,
            "is_active": True,
        },
    )
    if not user.password:
        user.set_password("testpass123")
        user.save()
    return user


@pytest.fixture
def authenticated_client(test_user):
    """
    Session-authenticated Django test client compatible with Django Ninja.

    Uses Redis-backed session (SessionManager.create_session) and
    sets the HttpOnly session cookie — the same auth flow as real clients.
    This replaces the broken force_login() pattern.

    Usage:
        def test_my_endpoint(authenticated_client):
            response = authenticated_client.get("/api/v1/dogs/")
            assert response.status_code == 200
    """
    from django.test import Client

    client = Client(SERVER_NAME="localhost")
    authenticate_client(client, test_user)
    return client