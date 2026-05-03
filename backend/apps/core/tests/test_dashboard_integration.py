"""
Dashboard Integration Tests - Wellfond BMS
=============================================
Integration tests for dashboard API endpoints with full stack.

Phase 8: Dashboard & Finance Exports
Run: python -m pytest apps/core/tests/test_dashboard_integration.py -v
"""

import pytest
from conftest import authenticate_client
from datetime import date, timedelta
from decimal import Decimal

from apps.core.models import User, Entity
from apps.operations.models import Dog, Vaccination
from apps.breeding.models import Litter, BreedingRecord
from apps.sales.models import SalesAgreement, AgreementStatus


@pytest.mark.django_db
class TestDashboardAPIResponseStructure:
    """Test dashboard API returns correct response structure."""

    def setup_method(self):
        """Set up test data."""
        self.entity = Entity.objects.create(
            name="Test Entity",
            slug="test",
            code="TEST"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.entity
        )

    def test_dashboard_metrics_endpoint_returns_200(self, client):
        """Test GET /dashboard/metrics returns 200 for authenticated user."""
        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_response_has_required_top_level_keys(self, client):
        """Test response has all required top-level keys."""
        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        required_keys = ['role', 'entity_id', 'stats', 'alerts', 'nparks_countdown', 'recent_activity']
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    def test_stats_has_required_keys(self, client):
        """Test stats object has all required keys."""
        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        stats = data['stats']
        required_stat_keys = ['total_dogs', 'active_litters', 'pending_agreements', 'overdue_vaccinations']

        for key in required_stat_keys:
            assert key in stats, f"Missing stat key: {key}"
            assert isinstance(stats[key], int), f"{key} should be an integer"

    def test_nparks_countdown_has_required_keys(self, client):
        """Test nparks_countdown has all required keys."""
        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        countdown = data['nparks_countdown']
        required_keys = ['days', 'deadline_date', 'status']

        for key in required_keys:
            assert key in countdown, f"Missing countdown key: {key}"

    def test_alerts_is_array(self, client):
        """Test alerts is an array."""
        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        assert isinstance(data['alerts'], list)

    def test_recent_activity_is_array(self, client):
        """Test recent_activity is an array."""
        authenticate_client(client, self.user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        assert isinstance(data['recent_activity'], list)


@pytest.mark.django_db
class TestDashboardStatsCalculation:
    """Test dashboard statistics are calculated correctly."""

    def setup_method(self):
        """Set up test data."""
        self.entity = Entity.objects.create(
            name="Test Entity",
            slug="test",
            code="TEST"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.entity
        )

    def test_total_dogs_counts_active_only(self, client):
        """Test total_dogs only counts active dogs."""
        from apps.core.services.dashboard import get_entity_stats

        # Create active dog
        Dog.objects.create(
            microchip="ACTIVE001",
            name="Active Dog",
            breed="Poodle",
            dob=date(2020, 1, 1),
            gender="F",
            entity=self.entity,
            status=Dog.Status.ACTIVE
        )

        # Create retired dog
        Dog.objects.create(
            microchip="RETIRED001",
            name="Retired Dog",
            breed="Golden",
            dob=date(2015, 1, 1),
            gender="M",
            entity=self.entity,
            status=Dog.Status.RETIRED
        )

        stats = get_entity_stats(self.user)

        assert stats['total_dogs'] == 1  # Only active

    def test_overdue_vaccinations_counted_correctly(self, client):
        """Test overdue vaccinations are counted correctly."""
        from apps.core.services.dashboard import get_entity_stats

        dog = Dog.objects.create(
            microchip="VACCINE001",
            name="Vaccine Test",
            breed="Poodle",
            dob=date(2020, 1, 1),
            gender="F",
            entity=self.entity,
            status=Dog.Status.ACTIVE
        )

        # Create overdue vaccination
        Vaccination.objects.create(
            dog=dog,
            vaccine_name="DHPP",
            date_given=date(2023, 1, 1),
            due_date=date(2024, 1, 1),
            status=Vaccination.Status.OVERDUE
        )

        stats = get_entity_stats(self.user)

        assert stats['overdue_vaccinations'] >= 1

    def test_pending_agreements_counted_correctly(self, client):
        """Test pending agreements are counted correctly."""
        from apps.core.services.dashboard import get_entity_stats

        # Create draft agreement
        SalesAgreement.objects.create(
            type="B2C",
            status=AgreementStatus.DRAFT,
            entity=self.entity,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="test@example.com",
            buyer_address="Test Address",
            total_amount=Decimal("1000.00"),
            created_by=self.user
        )

        stats = get_entity_stats(self.user)

        assert stats['pending_agreements'] == 1


@pytest.mark.django_db
class TestDashboardRoleBasedContent:
    """Test dashboard returns role-appropriate content."""

    def setup_method(self):
        """Set up test data."""
        self.entity = Entity.objects.create(
            name="Test Entity",
            slug="test",
            code="TEST"
        )

    def test_management_sees_revenue_summary(self, client):
        """Test management users see revenue summary."""
        user = User.objects.create_user(
            username="mgmt",
            email="mgmt@example.com",
            password="testpass123",
            role=User.Role.MANAGEMENT,
            entity=self.entity
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        assert 'revenue_summary' in data

    def test_vet_sees_health_alerts(self, client):
        """Test vet users see health alerts."""
        user = User.objects.create_user(
            username="vetuser",
            email="vet@example.com",
            password="testpass123",
            role=User.Role.VET,
            entity=self.entity
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        assert 'health_alerts' in data

    def test_sales_sees_sales_pipeline(self, client):
        """Test sales users see sales pipeline."""
        user = User.objects.create_user(
            username="salesuser",
            email="sales@example.com",
            password="testpass123",
            role=User.Role.SALES,
            entity=self.entity
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        assert 'sales_pipeline' in data

    def test_ground_does_not_see_revenue(self, client):
        """Test ground users don't see revenue data."""
        user = User.objects.create_user(
            username="grounduser",
            email="ground@example.com",
            password="testpass123",
            role=User.Role.GROUND,
            entity=self.entity
        )

        authenticate_client(client, user)
        response = client.get("/api/v1/dashboard/metrics")
        data = response.json()

        assert 'revenue_summary' not in data


@pytest.mark.django_db
class TestDashboardCaching:
    """Test dashboard caching behavior."""

    def setup_method(self):
        """Set up test data."""
        self.entity = Entity.objects.create(
            name="Test Entity",
            slug="test",
            code="TEST"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=User.Role.ADMIN,
            entity=self.entity
        )

    def test_cached_response_matches_fresh_response(self, client):
        """Test cached response structure matches fresh response."""
        from apps.core.services.dashboard import get_cached_dashboard_metrics, get_dashboard_metrics

        # Get fresh metrics
        fresh = get_dashboard_metrics(self.user)

        # Get cached metrics
        cached = get_cached_dashboard_metrics(self.user)

        # Both should have same structure
        assert set(fresh.keys()) == set(cached.keys())


@pytest.mark.django_db
class TestNParksCountdown:
    """Test NParks countdown calculation."""

    def test_countdown_calculates_correctly(self):
        """Test countdown calculates days until month end."""
        from apps.core.services.dashboard import get_nparks_countdown

        countdown = get_nparks_countdown()

        assert 'days' in countdown
        assert 'deadline_date' in countdown
        assert 'status' in countdown

        # Days should be 0-31
        assert 0 <= countdown['days'] <= 31

        # Status should be one of expected values
        assert countdown['status'] in ['upcoming', 'due_soon', 'overdue']

    def test_overdue_status_when_days_zero(self):
        """Test status is overdue when days <= 0."""
        from unittest.mock import patch
        from apps.core.services.dashboard import get_nparks_countdown

        # Mock today to be last day of month
        with patch('apps.core.services.dashboard.date') as mock_date:
            mock_date.today.return_value = date(2026, 4, 30)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            countdown = get_nparks_countdown()

            assert countdown['status'] == 'overdue'

    def test_due_soon_status_when_days_less_than_4(self):
        """Test status is due_soon when days <= 3."""
        from unittest.mock import patch
        from apps.core.services.dashboard import get_nparks_countdown

        # Mock today to be 27th (3 days before month end)
        with patch('apps.core.services.dashboard.date') as mock_date:
            mock_date.today.return_value = date(2026, 4, 27)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            countdown = get_nparks_countdown()

            assert countdown['status'] == 'due_soon'
