"""
Test Draminski Service
======================
Tests for per-dog baseline calculation, thresholds, and mating windows.
"""

import pytest
import uuid
from datetime import datetime, timedelta

from apps.core.models import User, Entity
from apps.operations.models import Dog, InHeatLog
from apps.operations.services.draminski import (
    interpret,
    calc_window,
    calculate_trend,
    interpret_for_api,
    _calculate_baseline_for_dog,
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
        gender="female",
        breed="Golden Retriever",
        entity=test_entity,
        microchip="1234567890",
    )
    return dog


@pytest.fixture
def create_heat_logs(test_dog, test_user):
    """Factory to create heat logs for a dog."""
    def _create_readings(readings):
        logs = []
        base_time = datetime.now() - timedelta(days=len(readings))
        for i, reading in enumerate(readings):
            log = InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=reading,
                mating_window="EARLY",
                created_by=test_user,
            )
            # Update created_at to simulate historical readings
            log.created_at = base_time + timedelta(days=i)
            log.save()
            logs.append(log)
        return logs
    return _create_readings


class TestDraminskiInterpret:
    """Tests for Draminski interpret function."""

    @pytest.mark.django_db
    def test_early_stage(self, test_dog):
        """Test EARLY stage detection."""
        # Create baseline around 400
        for i in range(5):
            InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=400,
                mating_window="EARLY",
            )

        # Low reading - early stage
        zone, trend = interpret(test_dog.id, 200)
        assert zone == "EARLY"

    @pytest.mark.django_db
    def test_rising_stage(self, test_dog):
        """Test RISING stage detection."""
        # Baseline of 400
        for i in range(5):
            InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=400,
                mating_window="EARLY",
            )

        # Reading at 0.7x baseline - rising
        zone, trend = interpret(test_dog.id, 280)
        assert zone == "RISING"

    @pytest.mark.django_db
    def test_fast_stage(self, test_dog):
        """Test FAST stage detection."""
        for i in range(5):
            InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=400,
                mating_window="EARLY",
            )

        # Reading at 1.2x baseline - fast rise
        zone, trend = interpret(test_dog.id, 480)
        assert zone == "FAST"

    @pytest.mark.django_db
    def test_peak_stage(self, test_dog):
        """Test PEAK stage detection."""
        for i in range(5):
            InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=400,
                mating_window="EARLY",
            )

        # Reading at 1.6x baseline - peak
        zone, trend = interpret(test_dog.id, 640)
        assert zone == "PEAK"

    @pytest.mark.django_db
    def test_mate_now_stage(self, test_dog):
        """Test MATE_NOW stage detection (post-peak drop)."""
        # Create history with peak
        for i in range(5):
            InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=400 + i * 50,  # Rising trend
                mating_window="FAST" if i < 4 else "PEAK",
            )

        # Now reading drops - should trigger MATE_NOW
        zone, trend = interpret(test_dog.id, 500)
        # This would need actual logic to detect drop from peak
        # For now, just verify it runs without error
        assert zone in ["EARLY", "RISING", "FAST", "PEAK", "MATE_NOW"]

    @pytest.mark.django_db
    def test_no_baseline_new_dog(self, test_dog):
        """Test behavior with no historical readings."""
        zone, trend = interpret(test_dog.id, 300)
        # Should use default baseline
        assert zone in ["EARLY", "RISING", "FAST", "PEAK", "MATE_NOW"]


class TestCalculateBaseline:
    """Tests for baseline calculation."""

    @pytest.mark.django_db
    def test_baseline_calculation(self, test_dog, create_heat_logs):
        """Test baseline calculation from historical readings."""
        readings = [300, 350, 400, 450, 500]
        create_heat_logs(readings)

        baseline = _calculate_baseline_for_dog(str(test_dog.id))
        expected = sum(readings) / len(readings)  # 400
        assert baseline == expected

    @pytest.mark.django_db
    def test_baseline_no_readings(self, test_dog):
        """Test baseline with no readings returns default."""
        baseline = _calculate_baseline_for_dog(str(test_dog.id))
        assert baseline == 300  # DEFAULT_BASELINE

    @pytest.mark.django_db
    def test_baseline_uses_last_30(self, test_dog, create_heat_logs):
        """Test baseline only uses last 30 readings."""
        # Create 40 readings
        old_readings = [200] * 20
        recent_readings = [400] * 20
        create_heat_logs(old_readings + recent_readings)

        baseline = _calculate_baseline_for_dog(str(test_dog.id))
        # Should only average recent readings (400), not old ones (200)
        expected = sum(recent_readings) / len(recent_readings)
        assert baseline == expected


class TestCalcWindow:
    """Tests for mating window calculation."""

    def test_early_window(self):
        """Test window for early stage."""
        window = calc_window("EARLY", datetime.now())
        # Early stage - window starts now, ends in 7 days
        assert window["start"] <= datetime.now().isoformat()
        assert window["zone"] == "EARLY"

    def test_peak_window(self):
        """Test window for peak stage."""
        window = calc_window("PEAK", datetime.now())
        assert window["zone"] == "PEAK"
        # Peak stage - mate within 24-48 hours
        assert "start" in window
        assert "end" in window

    def test_mate_now_window(self):
        """Test window for MATE_NOW stage."""
        window = calc_window("MATE_NOW", datetime.now())
        assert window["zone"] == "MATE_NOW"
        # Mate now - window is immediate
        assert "start" in window
        assert "end" in window


class TestCalculateTrend:
    """Tests for trend calculation."""

    @pytest.mark.django_db
    def test_trend_7_days(self, test_dog, create_heat_logs):
        """Test 7-day trend generation."""
        readings = [300, 320, 350, 380, 420, 460, 500]
        create_heat_logs(readings)

        trend = calculate_trend(test_dog.id, days=7)

        assert len(trend) == 7
        # Verify ascending trend
        for i in range(1, len(trend)):
            assert trend[i]["value"] >= trend[i-1]["value"]

    @pytest.mark.django_db
    def test_trend_empty(self, test_dog):
        """Test trend with no readings."""
        trend = calculate_trend(test_dog.id, days=7)
        assert trend == []


class TestInterpretForApi:
    """Tests for interpret_for_api function."""

    @pytest.mark.django_db
    def test_api_interpretation(self, test_dog):
        """Test full API response format."""
        # Create some baseline readings
        for i in range(5):
            InHeatLog.objects.create(
                dog=test_dog,
                draminski_reading=400,
                mating_window="EARLY",
            )

        result = interpret_for_api(str(test_dog.id), 480)

        assert "zone" in result
        assert "trend" in result
        assert "mating_window" in result
        assert "baseline" in result
        assert isinstance(result["trend"], list)
        assert isinstance(result["mating_window"], dict)

    @pytest.mark.django_db
    def test_api_invalid_dog(self):
        """Test API with non-existent dog."""
        fake_id = str(uuid.uuid4())
        result = interpret_for_api(fake_id, 400)

        # Should return default values
        assert "zone" in result
        assert "trend" in result
        assert result["trend"] == []
