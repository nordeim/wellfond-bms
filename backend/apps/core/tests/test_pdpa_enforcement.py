"""
TDD: PDPA Enforcement in EntityScopingMiddleware
=================================================
Phase 2 — Verify that enforce_pdpa() is applied centrally.

Currently: enforce_pdpa() defined in core/permissions.py but never
called in any router, service, or middleware.
Customer list returns all customers regardless of PDPA consent.
"""

import pytest
from django.test import Client

from apps.core.models import Entity, User
from apps.customers.models import Customer


@pytest.fixture
def test_pdpa_entity(db):
    return Entity.objects.create(
        name="PDPA Test", code="PDPA", slug="pdpa-test"
    )


@pytest.fixture
def test_pdpa_user(db, test_pdpa_entity):
    return User.objects.create_user(
        username="pdpatester",
        email="pdpatester@test.com",
        password="testpass123",
        role=User.Role.MANAGEMENT,
        entity=test_pdpa_entity,
    )


@pytest.fixture
def opted_in_customer(db, test_pdpa_entity):
    return Customer.objects.create(
        name="Opted In",
        mobile="+6591000001",
        pdpa_consent=True,
        entity=test_pdpa_entity,
    )


@pytest.fixture
def opted_out_customer(db, test_pdpa_entity):
    return Customer.objects.create(
        name="Opted Out",
        mobile="+6591000002",
        pdpa_consent=False,
        entity=test_pdpa_entity,
    )


@pytest.fixture
def pdpa_authenticated_client(test_pdpa_user):
    from django.http import HttpRequest
    from apps.core.auth import SessionManager, AuthenticationService

    request = HttpRequest()
    request.META["SERVER_NAME"] = "localhost"
    request.META["SERVER_PORT"] = "8000"

    session_key, _ = SessionManager.create_session(test_pdpa_user, request)

    client = Client(SERVER_NAME="localhost")
    client.cookies[AuthenticationService.COOKIE_NAME] = session_key
    return client


class TestEnforcePdpa:
    """Verify PDPA hard filter is active at QuerySet level."""

    def test_enforce_pdpa_function_exists(self):
        from apps.core.permissions import enforce_pdpa
        assert callable(enforce_pdpa)

    def test_enforce_pdpa_filters_opted_out(
        self, opted_in_customer, opted_out_customer, test_pdpa_user
    ):
        from apps.core.permissions import enforce_pdpa

        qs = Customer.objects.all()
        filtered = enforce_pdpa(qs, test_pdpa_user)

        assert opted_in_customer in filtered
        assert opted_out_customer not in filtered, (
            "PDPA filter must exclude opted-out customers at QuerySet level"
        )

    def test_enforce_pdpa_preserves_other_filters(
        self, opted_in_customer, opted_out_customer, test_pdpa_user
    ):
        from apps.core.permissions import enforce_pdpa

        qs = Customer.objects.filter(name="Opted In")
        filtered = enforce_pdpa(qs, test_pdpa_user)

        assert opted_in_customer in filtered
        assert opted_out_customer not in filtered
        assert len(filtered) == 1