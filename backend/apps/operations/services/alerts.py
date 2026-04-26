"""
Alerts service for Wellfond BMS
==============================
Dashboard alert cards data provider.
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from apps.core.models import User
    from ..models import Dog


def get_vaccine_overdue(entity_id: str | None = None) -> List[dict]:
    """
    Get dogs with overdue vaccinations.
    
    Returns list of alert card data.
    """
    from ..models import Dog, Vaccination
    
    dogs = Dog.objects.filter(
        vaccinations__status=Vaccination.Status.OVERDUE
    ).distinct()
    
    if entity_id:
        dogs = dogs.filter(entity_id=entity_id)
    
    return [
        {
            "id": str(dog.id),
            "type": "vaccine_overdue",
            "title": f"{dog.name} - Vaccine Overdue",
            "count": dog.vaccinations.filter(status=Vaccination.Status.OVERDUE).count(),
            "dog": dog,
        }
        for dog in dogs[:10]  # Limit to 10 most recent
    ]


def get_vaccine_due_soon(days: int = 30, entity_id: str | None = None) -> List[dict]:
    """
    Get dogs with vaccinations due soon.
    """
    from ..models import Dog, Vaccination
    
    today = date.today()
    cutoff = today + timedelta(days=days)
    
    dogs = Dog.objects.filter(
        vaccinations__status=Vaccination.Status.DUE_SOON,
        vaccinations__due_date__lte=cutoff
    ).distinct()
    
    if entity_id:
        dogs = dogs.filter(entity_id=entity_id)
    
    return [
        {
            "id": str(dog.id),
            "type": "vaccine_due_soon",
            "title": f"{dog.name} - Vaccine Due Soon",
            "count": dog.vaccinations.filter(
                status=Vaccination.Status.DUE_SOON,
                due_date__lte=cutoff
            ).count(),
            "dog": dog,
        }
        for dog in dogs[:10]
    ]


def get_rehome_overdue(user: "User", entity_id: str | None = None) -> List[dict]:
    """
    Get dogs approaching or past rehome age.
    
    - Yellow: 5-6 years (approaching)
    - Red: 6+ years (overdue)
    """
    from ..models import Dog
    
    # Calculate date thresholds
    today = date.today()
    six_years_ago = today - timedelta(days=6 * 365)
    five_years_ago = today - timedelta(days=5 * 365)
    
    # Get dogs 5+ years old, active status
    dogs = Dog.objects.filter(
        dob__lte=five_years_ago,
        status=Dog.Status.ACTIVE
    ).order_by("dob")
    
    # Apply entity scoping (unless management)
    if user.role != "management" and user.entity_id:
        dogs = dogs.filter(entity_id=user.entity_id)
    elif entity_id:
        dogs = dogs.filter(entity_id=entity_id)
    
    alerts = []
    for dog in dogs:
        flag = dog.rehome_flag
        if flag:
            alerts.append({
                "id": str(dog.id),
                "type": "rehome_overdue",
                "title": f"{dog.name} - Rehome Age ({dog.age_display})",
                "count": 1,
                "color": "red" if flag == "red" else "yellow",
                "dog": dog,
            })
    
    return alerts[:10]


def get_in_heat(entity_id: str | None = None) -> List[dict]:
    """
    Get female dogs currently in heat (based on logs).
    
    This is a placeholder - actual implementation would query InHeatLog.
    """
    # TODO: Implement when InHeatLog model is created
    return []


def get_nursing_flags(entity_id: str | None = None) -> List[dict]:
    """
    Get active nursing flags.
    
    This is a placeholder - actual implementation would query NursingFlagLog.
    """
    # TODO: Implement when NursingFlagLog model is created
    return []


def get_8week_litters(entity_id: str | None = None) -> List[dict]:
    """
    Get litters approaching 8 weeks (ready for rehome).
    
    This is a placeholder - actual implementation would query Litter model.
    """
    # TODO: Implement when Litter model is created
    return []


def get_nparks_countdown(entity_id: str | None = None) -> int:
    """
    Get days until end of month (NParks submission deadline).
    """
    today = date.today()
    
    # Get last day of current month
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    
    last_day = next_month - timedelta(days=1)
    
    return (last_day - today).days


def get_missing_parents(entity_id: str | None = None) -> List[dict]:
    """
    Get dogs with incomplete pedigree (missing dam or sire).
    
    Useful for data quality alerts.
    """
    from ..models import Dog
    
    dogs = Dog.objects.filter(
        status=Dog.Status.ACTIVE
    ).filter(
        models.Q(dam__isnull=True) | models.Q(sire__isnull=True)
    )
    
    if entity_id:
        dogs = dogs.filter(entity_id=entity_id)
    
    return [
        {
            "id": str(dog.id),
            "type": "missing_parents",
            "title": f"{dog.name} - Incomplete Pedigree",
            "count": (1 if not dog.dam else 0) + (1 if not dog.sire else 0),
            "dog": dog,
        }
        for dog in dogs[:10]
    ]


from django.db import models


def get_all_alert_cards(user: "User", entity_id: str | None = None) -> List[dict]:
    """
    Get all dashboard alert cards.
    
    Args:
        user: Current user (for entity scoping)
        entity_id: Optional entity override (for management)
        
    Returns:
        List of alert cards sorted by priority
    """
    # Apply entity scoping
    if user.role != "management":
        entity_id = str(user.entity_id) if user.entity_id else None
    
    alerts = []
    
    # Vaccine overdue (red - highest priority)
    vaccine_overdue = get_vaccine_overdue(entity_id)
    for alert in vaccine_overdue:
        alerts.append({
            **alert,
            "color": "red",
            "priority": 1,
        })
    
    # Rehome overdue (red/yellow)
    rehome_alerts = get_rehome_overdue(user, entity_id)
    for alert in rehome_alerts:
        alerts.append({
            **alert,
            "priority": 2 if alert["color"] == "red" else 3,
        })
    
    # In heat (pink)
    heat_alerts = get_in_heat(entity_id)
    for alert in heat_alerts:
        alerts.append({
            **alert,
            "color": "pink",
            "priority": 4,
        })
    
    # 8-week litters (blue)
    litter_alerts = get_8week_litters(entity_id)
    for alert in litter_alerts:
        alerts.append({
            **alert,
            "color": "blue",
            "priority": 5,
        })
    
    # Nursing flags (orange)
    nursing_alerts = get_nursing_flags(entity_id)
    for alert in nursing_alerts:
        alerts.append({
            **alert,
            "color": "orange",
            "priority": 6,
        })
    
    # NParks countdown (navy)
    days_to_deadline = get_nparks_countdown(entity_id)
    if days_to_deadline <= 7:  # Only show if within a week
        alerts.append({
            "id": "nparks-countdown",
            "type": "nparks_countdown",
            "title": f"NParks Deadline in {days_to_deadline} days",
            "count": days_to_deadline,
            "color": "navy",
            "priority": 7,
        })
    
    # Sort by priority
    alerts.sort(key=lambda x: x["priority"])
    
    return alerts
