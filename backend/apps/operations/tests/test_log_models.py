"""
Test Ground Operations Log Models
==================================
TDD tests for all 7 ground log model types with validation and edge cases.
"""

import pytest
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import User, Entity
from apps.operations.models import (
    Dog,
    InHeatLog,
    MatedLog,
    WhelpedLog,
    WhelpedPup,
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
        gender="F",
        breed="Golden Retriever",
        entity=test_entity,
        microchip="1234567890",
        dob=date(2020, 1, 1),
    )
    return dog


@pytest.fixture
def test_sire(test_entity):
    """Create test sire dog."""
    dog = Dog.objects.create(
        name="Test Sire",
        gender="M",
        breed="Golden Retriever",
        entity=test_entity,
        microchip="0987654321",
        dob=date(2019, 1, 1),
    )
    return dog


class TestInHeatLog:
    """TDD tests for InHeatLog model."""

    @pytest.mark.django_db
    def test_create_in_heat_log_success(self, test_dog, test_user):
        """RED: Test creating a basic in-heat log."""
        # Initially this will fail if model doesn't exist
        log = InHeatLog.objects.create(
            dog=test_dog,
            draminski_reading=350,
            mating_window="RISING",
            notes="Test heat detection",
            created_by=test_user,
        )

        assert log.id is not None
        assert log.dog == test_dog
        assert log.draminski_reading == 350
        assert log.mating_window == "RISING"
        assert log.created_by == test_user
        assert log.created_at is not None

    @pytest.mark.django_db
    def test_in_heat_log_str_representation(self, test_dog, test_user):
        """Test string representation includes dog name and window."""
        log = InHeatLog.objects.create(
            dog=test_dog,
            draminski_reading=400,
            mating_window="PEAK",
            created_by=test_user,
        )

        expected = f"Heat log for {test_dog.name}: PEAK"
        assert str(log) == expected

    @pytest.mark.django_db
    def test_in_heat_log_required_fields(self, test_dog):
        """Test that required fields raise validation errors."""
        # Missing draminski_reading
        log = InHeatLog(
            dog=test_dog,
            mating_window="EARLY",
        )
        with pytest.raises(ValidationError):
            log.full_clean()

    @pytest.mark.django_db
    def test_in_heat_log_ordering(self, test_dog, test_user):
        """Test logs are ordered by created_at descending."""
        # Create logs at different times
        log1 = InHeatLog.objects.create(
            dog=test_dog,
            draminski_reading=300,
            mating_window="EARLY",
            created_by=test_user,
        )
        log1.created_at = timezone.now() - timedelta(days=2)
        log1.save()

        log2 = InHeatLog.objects.create(
            dog=test_dog,
            draminski_reading=400,
            mating_window="PEAK",
            created_by=test_user,
        )

        logs = InHeatLog.objects.filter(dog=test_dog)
        assert logs.first() == log2  # Most recent first


class TestMatedLog:
    """TDD tests for MatedLog model."""

    @pytest.mark.django_db
    def test_create_mated_log_success(self, test_dog, test_sire, test_user):
        """RED: Test creating a basic mating log."""
        log = MatedLog.objects.create(
            dog=test_dog,
            sire=test_sire,
            method="NATURAL",
            notes="Successful mating",
            created_by=test_user,
        )

        assert log.id is not None
        assert log.dog == test_dog
        assert log.sire == test_sire
        assert log.method == "NATURAL"
        assert log.sire2 is None  # Optional dual sire

    @pytest.mark.django_db
    def test_create_dual_sire_mating(self, test_dog, test_sire, test_entity, test_user):
        """Test dual-sire mating with second sire."""
        sire2 = Dog.objects.create(
            name="Second Sire",
            gender="M",
            breed="Golden Retriever",
            entity=test_entity,
            microchip="1111111111",
            dob=date(2019, 6, 1),
        )

        log = MatedLog.objects.create(
            dog=test_dog,
            sire=test_sire,
            method="ASSISTED",
            sire2=sire2,
            created_by=test_user,
        )

        assert log.sire2 == sire2
        assert str(log) == f"Mating for {test_dog.name} with {test_sire.name}"

    @pytest.mark.django_db
    def test_mated_log_method_choices(self, test_dog, test_sire, test_user):
        """Test method field only accepts valid choices."""
        log = MatedLog(
            dog=test_dog,
            sire=test_sire,
            method="INVALID",
            created_by=test_user,
        )

        with pytest.raises(ValidationError):
            log.full_clean()


class TestWhelpedLog:
    """TDD tests for WhelpedLog and WhelpedPup models."""

    @pytest.mark.django_db
    def test_create_whelped_log_success(self, test_dog, test_user):
        """RED: Test creating a whelping log."""
        log = WhelpedLog.objects.create(
            dog=test_dog,
            method="NATURAL",
            alive_count=5,
            stillborn_count=0,
            notes="Healthy litter",
            created_by=test_user,
        )

        assert log.id is not None
        assert log.dog == test_dog
        assert log.alive_count == 5
        assert log.stillborn_count == 0

    @pytest.mark.django_db
    def test_create_whelped_log_with_pups(self, test_dog, test_user):
        """Test whelped log with individual pup records."""
        log = WhelpedLog.objects.create(
            dog=test_dog,
            method="C_SECTION",
            alive_count=3,
            stillborn_count=0,
            created_by=test_user,
        )

        # Create pup records
        pup1 = WhelpedPup.objects.create(
            log=log,
            gender="M",
            colour="golden",
            birth_weight=Decimal("0.35"),
        )
        pup2 = WhelpedPup.objects.create(
            log=log,
            gender="F",
            colour="cream",
            birth_weight=Decimal("0.32"),
        )

        assert log.pups.count() == 2
        assert pup1 in log.pups.all()
        assert pup1.gender == "M"
        assert pup1.birth_weight == Decimal("0.35")

    @pytest.mark.django_db
    def test_whelped_pup_str(self, test_dog, test_user):
        """Test pup string representation."""
        log = WhelpedLog.objects.create(
            dog=test_dog,
            method="NATURAL",
            alive_count=1,
            created_by=test_user,
        )
        pup = WhelpedPup.objects.create(
            log=log,
            gender="F",
            colour="golden",
        )

        expected = f"Pup F from {test_dog.name}'s litter"
        assert str(pup) == expected


class TestHealthObsLog:
    """TDD tests for HealthObsLog model."""

    @pytest.mark.django_db
    def test_create_health_obs_log_success(self, test_dog, test_user):
        """RED: Test creating a health observation log."""
        log = HealthObsLog.objects.create(
            dog=test_dog,
            category="LIMPING",
            description="Mild limp on front left leg",
            temperature=Decimal("38.5"),
            weight=Decimal("28.5"),
            photos=["photo1.jpg", "photo2.jpg"],
            created_by=test_user,
        )

        assert log.id is not None
        assert log.category == "LIMPING"
        assert log.temperature == Decimal("38.5")
        assert log.photos == ["photo1.jpg", "photo2.jpg"]

    @pytest.mark.django_db
    def test_health_obs_category_choices(self, test_dog, test_user):
        """Test category field validation."""
        log = HealthObsLog(
            dog=test_dog,
            category="INVALID",
            description="Test",
            created_by=test_user,
        )

        with pytest.raises(ValidationError):
            log.full_clean()

    @pytest.mark.django_db
    def test_health_obs_temperature_range(self, test_dog, test_user):
        """Test temperature must be within valid range (35-45°C)."""
        log = HealthObsLog(
            dog=test_dog,
            category="OTHER",
            description="Test",
            temperature=Decimal("50.0"),  # Invalid: too high
            created_by=test_user,
        )

        with pytest.raises(ValidationError):
            log.full_clean()


class TestWeightLog:
    """TDD tests for WeightLog model."""

    @pytest.mark.django_db
    def test_create_weight_log_success(self, test_dog, test_user):
        """RED: Test creating a weight log."""
        log = WeightLog.objects.create(
            dog=test_dog,
            weight=Decimal("28.5"),
            created_by=test_user,
        )

        assert log.id is not None
        assert log.weight == Decimal("28.5")
        assert log.dog == test_dog

    @pytest.mark.django_db
    def test_weight_log_str(self, test_dog, test_user):
        """Test string representation."""
        log = WeightLog.objects.create(
            dog=test_dog,
            weight=Decimal("30.0"),
            created_by=test_user,
        )

        assert str(log) == f"Weight log for {test_dog.name}: 30.0 kg"


class TestNursingFlagLog:
    """TDD tests for NursingFlagLog model."""

    @pytest.mark.django_db
    def test_create_nursing_flag_success(self, test_dog, test_user):
        """RED: Test creating a nursing flag log."""
        log = NursingFlagLog.objects.create(
            dog=test_dog,
            section="MUM",
            flag_type="NO_MILK",
            severity="SERIOUS",
            photos=["photo1.jpg"],
            created_by=test_user,
        )

        assert log.id is not None
        assert log.section == "MUM"
        assert log.severity == "SERIOUS"

    @pytest.mark.django_db
    def test_nursing_flag_with_pup_number(self, test_dog, test_user):
        """Test nursing flag for specific pup."""
        log = NursingFlagLog.objects.create(
            dog=test_dog,
            section="PUP",
            pup_number=2,
            flag_type="PUP_NOT_FEEDING",
            severity="MONITORING",
            created_by=test_user,
        )

        assert log.section == "PUP"
        assert log.pup_number == 2
        assert log.flag_type == "PUP_NOT_FEEDING"

    @pytest.mark.django_db
    def test_nursing_flag_str(self, test_dog, test_user):
        """Test string representation."""
        log = NursingFlagLog.objects.create(
            dog=test_dog,
            section="MUM",
            flag_type="NO_MILK",
            severity="SERIOUS",
            created_by=test_user,
        )

        assert str(log) == f"Nursing flag for {test_dog.name}: NO_MILK (SERIOUS)"


class TestNotReadyLog:
    """TDD tests for NotReadyLog model."""

    @pytest.mark.django_db
    def test_create_not_ready_log_success(self, test_dog, test_user):
        """RED: Test creating a not-ready log."""
        expected_date = date.today() + timedelta(days=14)

        log = NotReadyLog.objects.create(
            dog=test_dog,
            notes="Not yet showing signs",
            expected_date=expected_date,
            created_by=test_user,
        )

        assert log.id is not None
        assert log.expected_date == expected_date
        assert log.notes == "Not yet showing signs"

    @pytest.mark.django_db
    def test_not_ready_log_optional_expected_date(self, test_dog, test_user):
        """Test expected_date is optional."""
        log = NotReadyLog.objects.create(
            dog=test_dog,
            notes="Check again later",
            created_by=test_user,
        )

        assert log.expected_date is None

    @pytest.mark.django_db
    def test_not_ready_log_str(self, test_dog, test_user):
        """Test string representation."""
        log = NotReadyLog.objects.create(
            dog=test_dog,
            notes="Test notes",
            created_by=test_user,
        )

        assert str(log) == f"Not ready log for {test_dog.name}"


class TestLogEntityScoping:
    """TDD tests for entity scoping across all log types."""

    @pytest.mark.django_db
    def test_logs_respect_entity_boundaries(
        self, test_dog, test_user, test_entity
    ):
        """Test that logs can only be created for dogs in user's entity."""
        # Create log for dog in same entity - should succeed
        log = InHeatLog.objects.create(
            dog=test_dog,
            draminski_reading=350,
            mating_window="RISING",
            created_by=test_user,
        )

        assert log.dog.entity == test_entity
        assert log.created_by.entity == test_entity
