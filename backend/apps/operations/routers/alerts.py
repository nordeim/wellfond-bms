"""
Alert Cards Endpoint - Wellfond BMS
=====================================
Dashboard alerts for vaccines, rehome, heat cycles, etc.
"""

from ninja import Router
from ninja.errors import HttpError

from apps.core.permissions import scope_entity
from apps.operations.models import Dog
from apps.operations.services.alerts import get_all_alert_cards, get_nparks_countdown

router = Router(tags=["alerts"])


def _get_current_user(request):
    """Get current user from session cookie."""
    from apps.core.auth import get_authenticated_user
    return get_authenticated_user(request)


@router.get("/", response=list[dict])
def list_alerts(request, entity: str = None):
    """
    Get all dashboard alert cards.
    
    Query params:
    - entity: Optional entity filter (management only)
    """
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    # Get alerts
    alerts = get_all_alert_cards(user, entity)
    
    return alerts


@router.get("/nparks-countdown")
def nparks_countdown(request):
    """
    Get days until NParks submission deadline.
    """
    return {"days": get_nparks_countdown()}


@router.get("/vaccines-overdue", response=list[dict])
def vaccines_overdue(request, entity: str = None):
    """
    Get dogs with overdue vaccinations.
    """
    from apps.operations.services.alerts import get_vaccine_overdue
    
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    # Apply entity scoping
    if user.role != 'management':
        entity = str(user.entity_id) if user.entity_id else None
    
    alerts = get_vaccine_overdue(entity)
    
    return [
        {
            "id": alert["id"],
            "type": alert["type"],
            "title": alert["title"],
            "count": alert["count"],
        }
        for alert in alerts
    ]


@router.get("/rehome-overdue", response=list[dict])
def rehome_overdue(request, entity: str = None):
    """
    Get dogs approaching or past rehome age.
    """
    from apps.operations.services.alerts import get_rehome_overdue
    
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    alerts = get_rehome_overdue(user, entity)
    
    return [
        {
            "id": alert["id"],
            "type": alert["type"],
            "title": alert["title"],
            "count": alert["count"],
            "color": alert.get("color"),
        }
        for alert in alerts
    ]
