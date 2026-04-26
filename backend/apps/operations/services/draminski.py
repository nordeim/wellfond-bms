"""
Draminski DOD2 Interpreter Service
=====================================
Per-dog threshold interpreter for heat cycle detection.
Pure math, no AI.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import Dog, InHeatLog


# Threshold multipliers (relative to dog's baseline)
EARLY_THRESHOLD = 0.5  # < 50% of baseline = early
RISING_MIN = 0.5       # 50% of baseline
RISING_MAX = 1.0       # 100% of baseline
FAST_MIN = 1.0         # 100% of baseline
FAST_MAX = 1.5         # 150% of baseline
PEAK_MULTIPLIER = 1.5  # > 150% of baseline = peak
DROP_THRESHOLD = 0.9     # Post-peak drop > 10% = MATE NOW


@dataclass
class TrendPoint:
    """Single point in 7-day trend array."""
    date: date
    reading: int
    zone: str


@dataclass
class DraminskiResult:
    """Complete Draminski interpretation result."""
    reading: int
    baseline: float
    zone: str
    mating_window: Optional[str]
    trend: List[TrendPoint]
    recommendation: str


def calculate_baseline(dog_id: str) -> float:
    """
    Calculate per-dog baseline from last 30 days of readings.
    
    Args:
        dog_id: UUID of the dog
        
    Returns:
        Mean of last 30 readings (or fewer if not available)
    """
    from ..models import InHeatLog
    
    # Get last 30 days of readings
    cutoff_date = date.today() - timedelta(days=30)
    logs = InHeatLog.objects.filter(
        dog_id=dog_id,
        created_at__date__gte=cutoff_date
    ).order_by('-created_at')[:30]
    
    if not logs:
        # Default baseline for new dogs
        return 250.0
    
    readings = [log.draminski_reading for log in logs]
    return sum(readings) / len(readings)


def get_historical_readings(dog_id: str, days: int = 7) -> List[dict]:
    """
    Get historical readings for trend calculation.
    
    Args:
        dog_id: UUID of the dog
        days: Number of days to look back
        
    Returns:
        List of dicts with date and reading
    """
    from ..models import InHeatLog
    
    cutoff_date = date.today() - timedelta(days=days)
    logs = InHeatLog.objects.filter(
        dog_id=dog_id,
        created_at__date__gte=cutoff_date
    ).order_by('created_at')
    
    return [
        {
            'date': log.created_at.date(),
            'reading': log.draminski_reading,
        }
        for log in logs
    ]


def get_peak_reading(dog_id: str, days: int = 30) -> Optional[int]:
    """
    Get highest reading in the last N days.
    
    Args:
        dog_id: UUID of the dog
        days: Number of days to look back
        
    Returns:
        Highest reading or None if no logs
    """
    from ..models import InHeatLog
    
    cutoff_date = date.today() - timedelta(days=days)
    logs = InHeatLog.objects.filter(
        dog_id=dog_id,
        created_at__date__gte=cutoff_date
    )
    
    if not logs:
        return None
    
    return max(log.draminski_reading for log in logs)


def interpret_reading(reading: int, baseline: float, peak: Optional[int]) -> tuple[str, Optional[str]]:
    """
    Interpret a single reading against thresholds.
    
    Args:
        reading: Current Draminski reading
        baseline: Dog's calculated baseline
        peak: Highest reading in last 30 days (or None)
        
    Returns:
        Tuple of (zone, mating_window)
    """
    ratio = reading / baseline if baseline > 0 else 0
    
    # Check for post-peak drop
    if peak and reading < peak * DROP_THRESHOLD and reading > baseline * FAST_MIN:
        return "MATE_NOW", "Mate Now - Post Peak Drop Detected"
    
    # Determine zone based on baseline ratio
    if ratio < EARLY_THRESHOLD:
        return "EARLY", "Early - Continue Monitoring"
    elif RISING_MIN <= ratio < RISING_MAX:
        return "RISING", "Rising - Daily Readings Recommended"
    elif FAST_MIN <= ratio < FAST_MAX:
        return "FAST", "Fast - Monitor Closely"
    elif ratio >= PEAK_MULTIPLIER:
        # Check if this is a new peak
        if peak is None or reading >= peak:
            return "PEAK", "Peak - Highest Recorded"
        else:
            # Post-peak but not yet dropped enough
            return "PEAK", "Peak - Monitor for Drop"
    
    # Default to early if below all thresholds
    return "EARLY", "Early - Continue Monitoring"


def calculate_trend(dog_id: str, baseline: float) -> List[TrendPoint]:
    """
    Generate 7-day trend array.
    
    Args:
        dog_id: UUID of the dog
        baseline: Dog's calculated baseline
        
    Returns:
        List of TrendPoint for last 7 days
    """
    historical = get_historical_readings(dog_id, days=7)
    
    trend = []
    for entry in historical:
        ratio = entry['reading'] / baseline if baseline > 0 else 0
        
        if ratio < EARLY_THRESHOLD:
            zone = "early"
        elif ratio < RISING_MAX:
            zone = "rising"
        elif ratio < FAST_MAX:
            zone = "fast"
        else:
            zone = "peak"
        
        trend.append(TrendPoint(
            date=entry['date'],
            reading=entry['reading'],
            zone=zone
        ))
    
    return trend


def get_recommendation(zone: str) -> str:
    """
    Get recommendation text based on zone.
    
    Args:
        zone: Calculated zone
        
    Returns:
        Human-readable recommendation
    """
    recommendations = {
        "EARLY": "Continue daily monitoring. Not yet in optimal mating window.",
        "RISING": "Take daily readings. Approaching optimal mating window.",
        "FAST": "Monitor closely. Mating window approaching.",
        "PEAK": "Peak detected. Monitor for post-peak drop (MATE NOW signal).",
        "MATE_NOW": "MATE NOW - Optimal breeding window. Post-peak drop detected.",
    }
    return recommendations.get(zone, "Continue monitoring.")


def interpret(dog_id: str, reading: int) -> DraminskiResult:
    """
    Complete Draminski interpretation for a reading.
    
    This is the main entry point for the Draminski service.
    Calculates per-dog baseline, determines zone, generates trend,
    and provides recommendation.
    
    Args:
        dog_id: UUID of the dog
        reading: Current Draminski DOD2 conductivity reading
        
    Returns:
        DraminskiResult with complete interpretation
    """
    # Calculate per-dog baseline (NOT global)
    baseline = calculate_baseline(dog_id)
    
    # Get historical peak
    peak = get_peak_reading(dog_id, days=30)
    
    # Interpret the reading
    zone, mating_window = interpret_reading(reading, baseline, peak)
    
    # Generate 7-day trend
    trend = calculate_trend(dog_id, baseline)
    
    # Get recommendation
    recommendation = get_recommendation(zone)
    
    return DraminskiResult(
        reading=reading,
        baseline=baseline,
        zone=zone,
        mating_window=mating_window,
        trend=trend,
        recommendation=recommendation,
    )


def calc_window(dog_id: str, history: List[dict]) -> dict:
    """
    Calculate mating window based on trend history.
    
    Args:
        dog_id: UUID of the dog
        history: List of historical readings with dates
        
    Returns:
        Dict with window info
    """
    if not history:
        return {
            "status": "insufficient_data",
            "message": "Need at least 3 days of readings",
        }
    
    # Need at least 3 data points
    if len(history) < 3:
        return {
            "status": "insufficient_data",
            "message": f"Have {len(history)} readings, need 3+",
        }
    
    # Calculate trend direction
    recent = history[-3:]  # Last 3 readings
    readings = [r['reading'] for r in recent]
    
    if readings[-1] > readings[0]:
        trend_direction = "rising"
    elif readings[-1] < readings[0]:
        trend_direction = "falling"
    else:
        trend_direction = "stable"
    
    # Get current interpretation
    current_reading = history[-1]['reading']
    result = interpret(dog_id, current_reading)
    
    return {
        "status": "calculated",
        "trend_direction": trend_direction,
        "current_zone": result.zone,
        "days_to_peak": None,  # Could add prediction logic
        "recommendation": result.recommendation,
    }


# Convenience function for API endpoints
def interpret_for_api(dog_id: str, reading: int) -> dict:
    """
    Interpret Draminski reading and return API-friendly dict.
    
    Args:
        dog_id: UUID of the dog
        reading: Draminski DOD2 reading
        
    Returns:
        Dict suitable for JSON serialization
    """
    result = interpret(dog_id, reading)
    
    return {
        "reading": result.reading,
        "baseline": round(result.baseline, 2),
        "zone": result.zone,
        "mating_window": result.mating_window,
        "trend": [
            {
                "date": tp.date.isoformat(),
                "reading": tp.reading,
                "zone": tp.zone,
            }
            for tp in result.trend
        ],
        "recommendation": result.recommendation,
    }
