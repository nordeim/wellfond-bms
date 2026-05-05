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
            "dog_id": str(dog.id),
            "dog_name": dog.name,
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
            "dog_id": str(dog.id),
            "dog_name": dog.name,
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
                "dog_id": str(dog.id),
                "dog_name": dog.name,
            })
    
    return alerts[:10]


def get_in_heat(entity_id: str | None = None) -> List[dict]:
    """
    Get female dogs currently in heat (based on recent InHeatLog entries).
    """
    from ..models import Dog, InHeatLog

    # Get recent heat logs (last 7 days)
    cutoff = date.today() - timedelta(days=7)
    logs = InHeatLog.objects.filter(
        created_at__date__gte=cutoff,
        dog__gender=Dog.Gender.FEMALE,
    ).select_related('dog')

    if entity_id:
        logs = logs.filter(dog__entity_id=entity_id)

    # Get unique dogs with their most recent heat status
    seen_dogs = set()
    alerts = []

    for log in logs.order_by('-created_at'):
        if log.dog_id not in seen_dogs:
            seen_dogs.add(log.dog_id)
            alerts.append({
                "id": str(log.id),
                "type": "in_heat",
                "title": f"{log.dog.name} - In Heat ({log.mating_window})",
                "count": 1,
                "dog_id": str(log.dog.id),
                "dog_name": log.dog.name,
                "mating_window": log.mating_window,
            })

    return alerts[:10]


def get_nursing_flags(entity_id: str | None = None) -> List[dict]:
    """
    Get active nursing flags (unresolved NursingFlagLog entries).
    """
    from ..models import NursingFlagLog

    # Get recent serious nursing flags (last 7 days)
    cutoff = date.today() - timedelta(days=7)
    logs = NursingFlagLog.objects.filter(
        created_at__date__gte=cutoff,
        severity=NursingFlagLog.Severity.SERIOUS,
    ).select_related('dog')

    if entity_id:
        logs = logs.filter(dog__entity_id=entity_id)

    return [
        {
            "id": str(log.id),
            "type": "nursing_flag",
            "title": f"{log.dog.name} - {log.flag_type}",
            "count": 1,
            "dog_id": str(log.dog.id),
            "dog_name": log.dog.name,
            "severity": log.severity,
            "flag_type": log.flag_type,
        }
        for log in logs[:10]
    ]


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
            "dog_id": str(dog.id),
            "dog_name": dog.name,
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


# =============================================================================
# Phase 3: SSE Event Generators
# =============================================================================


def get_pending_alerts(user: "User") -> List[dict]:
    """
    Get pending alerts for SSE stream.

    Returns alerts that have not been acknowledged.
    Deduplicates by dog+type.

    Args:
        user: Current user for entity scoping

    Returns:
        List of alert events for SSE
    """
    entity_id = str(user.entity_id) if user.entity_id and user.role != "management" else None

    events = []

    # Nursing flags (highest priority for SSE)
    nursing = get_nursing_flags(entity_id)
    for alert in nursing:
        events.append({
            "id": f"nursing-{alert['dog_id']}",
            "type": "nursing_flag",
            "title": alert["title"],
            "dog_id": alert["dog_id"],
            "dog_name": alert["dog_name"],
            "severity": alert.get("severity"),
            "timestamp": date.today().isoformat(),
        })

    # Heat cycles
    heat = get_in_heat(entity_id)
    for alert in heat:
        events.append({
            "id": f"heat-{alert['dog_id']}",
            "type": "heat_cycle",
            "title": alert["title"],
            "dog_id": alert["dog_id"],
            "dog_name": alert["dog_name"],
            "mating_window": alert.get("mating_window"),
            "timestamp": date.today().isoformat(),
        })

    # Vaccine overdue
    vaccines = get_vaccine_overdue(entity_id)
    for alert in vaccines:
        events.append({
            "id": f"vaccine-{alert['dog_id']}",
            "type": "overdue_vaccine",
            "title": alert["title"],
            "dog_id": alert["dog_id"],
            "dog_name": alert["dog_name"],
            "count": alert["count"],
            "timestamp": date.today().isoformat(),
        })

    # Rehome overdue
    rehome = get_rehome_overdue(user, entity_id)
    for alert in rehome:
        events.append({
            "id": f"rehome-{alert['dog_id']}",
            "type": "rehome_overdue",
            "title": alert["title"],
            "dog_id": alert["dog_id"],
            "dog_name": alert["dog_name"],
            "color": alert.get("color"),
            "timestamp": date.today().isoformat(),
        })

    return events


def create_alert_event(log_type: str, log_instance) -> dict:
    """
    Create a standardized alert event from a log instance.

    Args:
        log_type: Type of log (in_heat, nursing_flag, etc.)
        log_instance: The log model instance

    Returns:
        Alert event dict for SSE
    """
    event_types = {
        "in_heat": "heat_cycle",
        "mated": "mating_complete",
        "whelped": "litter_born",
        "health_obs": "health_observation",
        "weight": "weight_recorded",
        "nursing_flag": "nursing_flag",
        "not_ready": "not_ready",
    }

    return {
        "id": f"{log_type}-{log_instance.id}",
        "type": event_types.get(log_type, "alert"),
        "title": f"{log_instance.dog.name} - {log_type.replace('_', ' ').title()}",
        "dog_id": str(log_instance.dog.id),
        "dog_name": log_instance.dog.name,
        "timestamp": log_instance.created_at.isoformat(),
    }


def should_notify(log_type: str, log_instance) -> bool:
    """
    Determine if a log should trigger an SSE notification.

    Args:
        log_type: Type of log
        log_instance: The log model instance

    Returns:
        True if notification should be sent
    """
    from ..models import NursingFlagLog

    # Always notify for serious nursing flags
    if log_type == "nursing_flag" and isinstance(log_instance, NursingFlagLog):
        return log_instance.severity == NursingFlagLog.Severity.SERIOUS

    # Always notify for MATE_NOW in-heat readings
    if log_type == "in_heat":
        return log_instance.mating_window == "MATE_NOW"

    # Don't notify for routine logs
    return False
