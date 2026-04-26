"""
Test Ground Operations Logs Router
==================================
Tests for all 7 log types with idempotency and entity scoping.
"""

import json
import uuid
from datetime import date

import pytest
from django.test import Client
from django.core.cache import cache

from apps.core.models import User, Entity
from apps.operations.models import (
    Dog,
    InHeatLog,
    MatedLog,
    WhelpedLog,
    HealthObsLog,
    WeightLog,
    NursingFlagLog,
    NotReadyLog,
)


@pytest.fixture
def test_entity():
    """Create test entity."""
    entity, _ = Entity.objects.get_or_create(
        id=uuid.uuid4(),
        defaults={"name": "Test Entity", "code": "TEST"},
    )
    return entity


@pytest.fixture
def test_user(test_entity):
    """Create test user."""
    user = User.objects.create_user(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email="test@example.com",
        password="testpass123",
        role="ground",
        entity=test_entity,
    )
    return user


@pytest.fixture
def test_dog(test_entity):
    """Create test dog."""
    dog = Dog.objects.create(
        name="Test Dog",
        gender="F",  # Use choice value, not display value
        breed="Golden Retriever",
        entity=test_entity,
        microchip="1234567890",
        dob=date(2020, 1, 1),  # Add required dob field
    )
    return dog


@pytest.fixture
def test_sire(test_entity):
    """Create test sire dog."""
    dog = Dog.objects.create(
        name="Test Sire",
        gender="M",  # Use choice value, not display value
        breed="Golden Retriever",
        entity=test_entity,
        microchip="0987654321",
        dob=date(2019, 1, 1),  # Add required dob field
    )
    return dog


@pytest.fixture
def api_client():
    """Create test client."""
    return Client()


@pytest.fixture
def idempotency_key():
    """Generate unique idempotency key."""
    return f"test-key-{uuid.uuid4().hex}"


@pytest.fixture
def authenticated_client(test_user):
    """Create authenticated client with session cookie."""
    from django.test import Client
    from apps.core.auth import SessionManager, AuthenticationService
    from django.http import HttpRequest

    # Create a mock request for session creation
    request = HttpRequest()
    request.method = "POST"
    request.META["SERVER_NAME"] = "localhost"
    request.META["SERVER_PORT"] = "8000"

    # Create session in Redis
    session_key, csrf_token = SessionManager.create_session(test_user, request)

    # Create client with session cookie
    client = Client()
    client.cookies[AuthenticationService.COOKIE_NAME] = session_key

    return client


class TestInHeatLogs:
    """Tests for in-heat log endpoints."""

    @pytest.mark.django_db
    def test_create_in_heat_log_success(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test successful in-heat log creation."""

        response = authenticated_client.post(
            f"/api/v1/ground-logs/in-heat/{test_dog.id}",
            data=json.dumps({
                "draminski_reading": 350,
                "notes": "Test heat detection",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["dog_id"] == str(test_dog.id)
        assert data["draminski_reading"] == 350
        assert "mating_window" in data

    @pytest.mark.django_db
    def test_create_in_heat_log_idempotency(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test idempotency - duplicate requests return 200."""
        # First request
        response1 = authenticated_client.post(
            f"/api/v1/ground-logs/in-heat/{test_dog.id}",
            data=json.dumps({
                "draminski_reading": 350,
                "notes": "Test",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )
        assert response1.status_code == 200
        data1 = json.loads(response1.content)

        # Duplicate request - should also succeed (idempotency)
        response2 = authenticated_client.post(
            f"/api/v1/ground-logs/in-heat/{test_dog.id}",
            data=json.dumps({
                "draminski_reading": 350,
                "notes": "Test",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )
        assert response2.status_code == 200
        # Both responses should be identical due to idempotency
        data2 = json.loads(response2.content)
        assert data2["dog_id"] == data1["dog_id"]

    @pytest.mark.django_db
    def test_create_in_heat_log_no_auth(
        self, api_client, test_dog, idempotency_key
    ):
        """Test unauthorized request fails."""
        response = api_client.post(
            f"/api/v1/ground-logs/in-heat/{test_dog.id}",
            data=json.dumps({
                "draminski_reading": 350,
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )
        assert response.status_code == 401


class TestMatedLogs:
    """Tests for mated log endpoints."""

    @pytest.mark.django_db
    def test_create_mated_log_success(
        self, authenticated_client, test_dog, test_sire, idempotency_key
    ):
        """Test successful mated log creation."""
        response = authenticated_client.post(
            f"/api/v1/ground-logs/mated/{test_dog.id}",
            data=json.dumps({
                "sire_chip": test_sire.microchip,
                "method": "NATURAL",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["sire_id"] == str(test_sire.id)
        assert data["sire_name"] == test_sire.name
        assert data["method"] == "NATURAL"

    @pytest.mark.django_db
    def test_create_mated_log_invalid_sire(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test mated log with invalid sire chip fails."""
        response = authenticated_client.post(
            f"/api/v1/ground-logs/mated/{test_dog.id}",
            data=json.dumps({
                "sire_chip": "INVALID_CHIP",
                "method": "natural",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 422


class TestWhelpedLogs:
    """Tests for whelped log endpoints."""

    @pytest.mark.django_db
    def test_create_whelped_log_success(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test successful whelped log creation with pups."""
        response = authenticated_client.post(
            f"/api/v1/ground-logs/whelped/{test_dog.id}",
            data=json.dumps({
                "method": "NATURAL",
                "alive_count": 3,
                "stillborn_count": 0,
                "pups": [
                    {"gender": "M", "colour": "golden", "birth_weight": 0.35},
                    {"gender": "F", "colour": "golden", "birth_weight": 0.32},
                    {"gender": "M", "colour": "cream", "birth_weight": 0.34},
                ],
                "notes": "Healthy litter",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["alive_count"] == 3
        assert len(data["pups"]) == 3
        assert data["pups"][0]["birth_weight"] == 0.35


class TestHealthObsLogs:
    """Tests for health observation log endpoints."""

    @pytest.mark.django_db
    def test_create_health_obs_log_success(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test successful health observation log creation."""
        response = authenticated_client.post(
            f"/api/v1/ground-logs/health-obs/{test_dog.id}",
            data=json.dumps({
                "category": "LIMPING",
                "description": "Mild limp on front left leg",
                "temperature": 38.5,
                "weight": 28.5,
                "photos": ["photo1.jpg", "photo2.jpg"],
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["category"] == "LIMPING"
        assert data["temperature"] == 38.5


class TestWeightLogs:
    """Tests for weight log endpoints."""

    @pytest.mark.django_db
    def test_create_weight_log_success(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test successful weight log creation."""
        response = authenticated_client.post(
            f"/api/v1/ground-logs/weight/{test_dog.id}",
            data=json.dumps({
                "weight": 28.5,
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["weight"] == 28.5


class TestNursingFlagLogs:
    """Tests for nursing flag log endpoints."""

    @pytest.mark.django_db
    def test_create_nursing_flag_log_success(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test successful nursing flag log creation."""
        response = authenticated_client.post(
            f"/api/v1/ground-logs/nursing-flag/{test_dog.id}",
            data=json.dumps({
                "section": "MUM",
                "flag_type": "NO_MILK",
                "severity": "SERIOUS",
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["section"] == "MUM"
        assert data["severity"] == "SERIOUS"


class TestNotReadyLogs:
    """Tests for not-ready log endpoints."""

    @pytest.mark.django_db
    def test_create_not_ready_log_success(
        self, authenticated_client, test_dog, idempotency_key
    ):
        """Test successful not-ready log creation."""
        expected_date = date.today().isoformat()

        response = authenticated_client.post(
            f"/api/v1/ground-logs/not-ready/{test_dog.id}",
            data=json.dumps({
                "notes": "Not yet showing signs",
                "expected_date": expected_date,
            }),
            content_type="application/json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key,
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["expected_date"] == expected_date


class TestLogsList:
    """Tests for logs list endpoint."""

    @pytest.mark.django_db
    def test_list_logs_success(
        self, authenticated_client, test_user, test_dog
    ):
        """Test successful logs listing."""
        # Create some logs
        InHeatLog.objects.create(
            dog=test_dog,
            draminski_reading=350,
            created_by=test_user,
        )
        WeightLog.objects.create(
            dog=test_dog,
            weight=28.5,
            created_by=test_user,
        )

        response = authenticated_client.get(
            f"/api/v1/ground-logs/{test_dog.id}",
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] == 2
        assert len(data["results"]) == 2
