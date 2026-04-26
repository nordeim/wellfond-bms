"""
Vaccine service for Wellfond BMS
================================
Due date calculation for vaccinations.
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.db.models import QuerySet

if TYPE_CHECKING:
    from ..models import Dog, Vaccination


# Standard vaccine intervals (in days)
VACCINE_INTERVALS = {
    # Puppy series (DHPP/DHLPP)
    "DHPP": 21,
    "DHLPP": 21,
    "DHPPI": 21,
    "PUPPY_DHPP": 21,
    
    # Core vaccines (annual)
    "RABIES": 365,
    "DHPP_BOOSTER": 365,
    "DHLPP_BOOSTER": 365,
    "BORDETELLA": 365,
    
    # Non-core (as needed)
    "LEPTOSPIROSIS": 365,
    "LYME": 365,
    "INFLUENZA": 365,
    
    # Default for unknown vaccines
    "DEFAULT": 365,
}

# Vaccines that require series for puppies
PUPPY_SERIES_VACCINES = ["DHPP", "DHLPP", "DHPPI", "PUPPY_DHPP"]


def get_vaccine_interval(vaccine_name: str) -> int:
    """
    Get the interval in days for a vaccine.
    
    Args:
        vaccine_name: Name of the vaccine
        
    Returns:
        Interval in days
    """
    name_upper = vaccine_name.upper()
    
    # Check for exact match
    if name_upper in VACCINE_INTERVALS:
        return VACCINE_INTERVALS[name_upper]
    
    # Check for partial matches
    for key, interval in VACCINE_INTERVALS.items():
        if key in name_upper:
            return interval
    
    # Default to annual
    return VACCINE_INTERVALS["DEFAULT"]


def calc_vaccine_due(
    dog: "Dog",
    vaccine_name: str,
    date_given: date,
    previous_doses: int = 0
) -> date:
    """
    Calculate the next due date for a vaccination.
    
    For puppy series vaccines:
    - First 2-3 doses: 21 days apart
    - After series complete: annual boosters
    
    For adult dogs:
    - Annual boosters
    
    Args:
        dog: The dog receiving the vaccine
        vaccine_name: Name of the vaccine
        date_given: Date the vaccine was given
        previous_doses: Number of previous doses of this vaccine
        
    Returns:
        Calculated due date
    """
    interval = get_vaccine_interval(vaccine_name)
    name_upper = vaccine_name.upper()
    
    # Check if this is a puppy series vaccine
    is_puppy_series = any(v in name_upper for v in PUPPY_SERIES_VACCINES)
    
    if is_puppy_series:
        # Puppy series: 21 days between doses, then annual
        age_weeks = dog.age_years * 52
        
        if age_weeks < 16 and previous_doses < 3:
            # Still in puppy series
            return date_given + timedelta(days=21)
        else:
            # Series complete or adult - annual
            return date_given + timedelta(days=365)
    
    # Standard interval
    return date_given + timedelta(days=interval)


def get_overdue_vaccines(entity_id: str | None = None) -> QuerySet:
    """
    Get all overdue vaccinations.
    
    Args:
        entity_id: Optional entity filter
        
    Returns:
        QuerySet of overdue vaccinations
    """
    from ..models import Vaccination
    
    today = date.today()
    qs = Vaccination.objects.filter(
        status=Vaccination.Status.OVERDUE
    ).select_related("dog")
    
    if entity_id:
        qs = qs.filter(dog__entity_id=entity_id)
    
    return qs


def get_due_soon_vaccines(days: int = 30, entity_id: str | None = None) -> QuerySet:
    """
    Get vaccinations due within the specified days.
    
    Args:
        days: Number of days to look ahead
        entity_id: Optional entity filter
        
    Returns:
        QuerySet of vaccinations due soon
    """
    from ..models import Vaccination
    
    today = date.today()
    cutoff = today + timedelta(days=days)
    
    qs = Vaccination.objects.filter(
        status=Vaccination.Status.DUE_SOON,
        due_date__lte=cutoff
    ).select_related("dog")
    
    if entity_id:
        qs = qs.filter(dog__entity_id=entity_id)
    
    return qs


def get_next_vaccine_due(dog: "Dog") -> date | None:
    """
    Get the next due date for any vaccine for a dog.
    
    Args:
        dog: The dog to check
        
    Returns:
        The earliest due date, or None if no vaccines
    """
    upcoming = dog.vaccinations.filter(
        status__in=["UP_TO_DATE", "DUE_SOON"]
    ).order_by("due_date").first()
    
    if upcoming:
        return upcoming.due_date
    return None


def is_vaccination_current(dog: "Dog") -> bool:
    """
    Check if a dog's vaccinations are current.
    
    A dog is current if:
    - No overdue vaccines
    - At least one vaccine on record (or under 8 weeks old)
    
    Args:
        dog: The dog to check
        
    Returns:
        True if vaccinations are current
    """
    # Check for overdue vaccines
    has_overdue = dog.vaccinations.filter(status="OVERDUE").exists()
    
    if has_overdue:
        return False
    
    # Puppies under 8 weeks don't need vaccines yet
    if dog.age_years < (8 / 52):  # 8 weeks
        return True
    
    # Check if any vaccines exist
    return dog.vaccinations.exists()
