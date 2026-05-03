"""
Dashboard Tests - Wellfond BMS
================================
TDD test suite for dashboard metrics endpoint.
Phase 8: Dashboard & Finance Exports

Run: python -m pytest apps/core/tests/test_dashboard.py -v
"""

import pytest
from conftest import authenticate_client
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from apps.core.models import User, Entity
from apps.core.tests.factories import UserFactory
from apps.operations.models import Dog, Vaccination
from apps.breeding.models import Litter, Puppy, BreedingRecord
from apps.sales.models import SalesAgreement


@pytest.mark.django_db
class TestDashboardMetricsEndpoint:
    """Test GET /dashboard/metrics endpoint with role-based access."""

    def setup_method(self):
        """Set up test data."""
        self.holdings = Entity.objects.create(
            name="Holdings",
            slug="holdings",
            code="HOLDINGS"
        )
        self.katong = Entity.objects.create(
            name="Katong",
            slug="katong",
            code="KATONG"
        )

    def test_unauthenticated_request_returns_401(self, client):
        """Test that unauthenticated requests get 401."""
        response = client.get("/api/v1/dashboard/metrics")
        assert response.status_code == 401

    def test_management_user_sees_all_entities(self, client, django_user_model):
        """Test management role sees data from all entities."""
        # Create management user
        user = django_user_model.objects.create_user(
            username="mgmt",
            email="mgmt@wellfond.sg",
            password="testpass123",
            role=User.Role.MANAGEMENT,
            entity=self.holdings
        )

        # Create dogs in both entities
        Dog.objects.create(
            microchip="123456789",
            name="Holdings Dog",
            breed="Poodle",
            dob=date(2020, 1, 1),
            gender="F",
            colour="White",
            entity=self.holdings,
            status=Dog.Status.ACTIVE
        )
        Dog.objects.create(
            microchip="987654321",
            name="Katong Dog",
            breed="Golden",
            dob=date(2019, 1, 1),
            gender="M",
            colour="Gold",
            entity=self.katong,
            status=Dog.Status.ACTIVE
        )

        # Login and request
        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_dogs"] == 2  # Sees both entities

    def test_admin_user_sees_only_their_entity(self, client, django_user_model):
        """Test admin role is scoped to their entity."""
        user = django_user_model.objects.create_user(
            username="admin1",
            email="admin@wellfond.sg",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.holdings
        )

        # Create dogs
        Dog.objects.create(
            microchip="111111111",
            name="Holdings Dog",
            breed="Poodle",
            dob=date(2020, 1, 1),
            gender="F",
            entity=self.holdings,
            status=Dog.Status.ACTIVE
        )
        Dog.objects.create(
            microchip="222222222",
            name="Katong Dog",
            breed="Golden",
            dob=date(2019, 1, 1),
            gender="M",
            entity=self.katong,
            status=Dog.Status.ACTIVE
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_dogs"] == 1  # Only Holdings dog

    def test_sales_user_sees_sales_focused_metrics(self, client, django_user_model):
        """Test sales role sees sales-pipeline focused dashboard."""
        user = django_user_model.objects.create_user(
            username="sales1",
            email="sales@wellfond.sg",
            password="testpass123",
            role=User.Role.SALES,
            entity=self.holdings
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()
        # Sales sees: pending agreements, revenue, recent sales
        assert "pending_agreements" in data["stats"]
        assert "revenue_summary" in data

    def test_vet_user_sees_health_focused_metrics(self, client, django_user_model):
        """Test vet role sees health-focused dashboard."""
        user = django_user_model.objects.create_user(
            username="vet1",
            email="vet@wellfond.sg",
            password="testpass123",
            role=User.Role.VET,
            entity=self.holdings
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()
        # Vet sees: overdue vaccines, health flags, upcoming checks
        assert "overdue_vaccinations" in data["stats"]
        assert "health_alerts" in data

    def test_response_includes_required_sections(self, client, django_user_model):
        """Test response contains all required dashboard sections."""
        user = django_user_model.objects.create_user(
            username="admin2",
            email="admin2@wellfond.sg",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.holdings
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()

        # Required sections per plan_dashboard_page.md
        assert "stats" in data
        assert "alerts" in data
        assert "npars_countdown" in data
        assert "recent_activity" in data
        assert "role" in data

    def test_nparks_countdown_calculated_correctly(self, client, django_user_model):
        """Test NParks countdown returns days until month end."""
        user = django_user_model.objects.create_user(
            username="admin3",
            email="admin3@wellfond.sg",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.holdings
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()

        # Countdown should be between 1-31
        assert 1 <= data["npars_countdown"]["days"] <= 31
        assert "status" in data["npars_countdown"]  # upcoming | due_soon | overdue

    def test_caching_returns_same_response_within_60s(self, client, django_user_model):
        """Test Redis caching - same response within 60s window."""
        user = django_user_model.objects.create_user(
            username="admin4",
            email="admin4@wellfond.sg",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.holdings
        )

        authenticate_client(client, user)

        # First request
        response1 = client.get("/api/v1/dashboard/metrics")
        assert response1.status_code == 200
        data1 = response1.json()

        # Second request (should be cached)
        response2 = client.get("/api/v1/dashboard/metrics")
        data2 = response2.json()

        assert data1 == data2


@pytest.mark.django_db
class TestDashboardStatsCalculation:
    """Test dashboard statistics calculation logic."""

    def setup_method(self):
        """Set up test entities and data."""
        self.holdings = Entity.objects.create(
            name="Holdings",
            slug="holdings",
            code="HOLDINGS"
        )
        self.user = User.objects.create_user(
            username="test",
            email="test@wellfond.sg",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.holdings
        )

    def test_total_dogs_counts_only_active(self):
        """Test total_dogs excludes retired/rehomed/deceased."""
        from apps.core.services.dashboard import get_dashboard_metrics

        # Active dogs
        Dog.objects.create(
            microchip="ACTIVE1",
            name="Active Dog",
            breed="Poodle",
            dob=date(2020, 1, 1),
            gender="F",
            entity=self.holdings,
            status=Dog.Status.ACTIVE
        )
        Dog.objects.create(
            microchip="RETIRED1",
            name="Retired Dog",
            breed="Golden",
            dob=date(2015, 1, 1),
            gender="M",
            entity=self.holdings,
            status=Dog.Status.RETIRED
        )

        metrics = get_dashboard_metrics(self.user)
        assert metrics["stats"]["total_dogs"] == 1  # Only active

    def test_overdue_vaccinations_counted(self):
        """Test overdue vaccinations count."""
        from apps.core.services.dashboard import get_dashboard_metrics

        dog = Dog.objects.create(
            microchip="VACCINETEST",
            name="Vaccine Test",
            breed="Poodle",
            dob=date(2020, 1, 1),
            gender="F",
            entity=self.holdings,
            status=Dog.Status.ACTIVE
        )

        # Create overdue vaccination
        Vaccination.objects.create(
            dog=dog,
            vaccine_name="DHPP",
            date_given=date(2023, 1, 1),  # Over 1 year ago
            due_date=date(2024, 1, 1),  # Overdue
            status=Vaccination.Status.OVERDUE
        )

        metrics = get_dashboard_metrics(self.user)
        assert metrics["stats"]["overdue_vaccinations"] >= 1


@pytest.mark.django_db
class TestActivityFeed:
    """Test recent activity feed."""

    def setup_method(self):
        """Set up test data."""
        self.entity = Entity.objects.create(
            name="Test Entity",
            slug="test",
            code="TEST"
        )
        self.user = User.objects.create_user(
            username="test",
            email="test@test.com",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.entity
        )

    def test_activity_feed_returns_recent_logs(self, client):
        """Test activity feed returns last 10 audit logs."""
        # Create audit logs
        from apps.core.models import AuditLog

        for i in range(15):
            AuditLog.objects.create(
                actor=self.user,
                action=AuditLog.Action.CREATE,
                resource_type="dog",
                resource_id=f"dog-{i}",
                payload={"name": f"Dog {i}"}
            )

        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()
        assert len(data["recent_activity"]) <= 10
