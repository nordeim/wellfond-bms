"""Dashboard service for Wellfond BMS
==============================
Role-aware metrics aggregation with Redis caching.

Implements Phase 8 dashboard requirements:
- Stats: total_dogs, active_litters, pending_agreements, overdue_vaccinations
- Alerts: from existing alerts service
- NParks countdown: days until month end
- Recent activity: last 10 audit logs
- Revenue summary: last 6 months from SalesAgreement
- Role-aware payload construction
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, List, Dict, Any

from django.core.cache import cache
from django.db.models import Count, Sum, Q

if TYPE_CHECKING:
    from apps.core.models import User
    from apps.core.models import AuditLog


CACHE_TTL = 60  # 60 seconds cache


def get_nparks_countdown() -> Dict[str, Any]:
    """Get days until NParks submission deadline (end of month)."""
    today = date.today()
    
    # Get last day of current month
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    
    last_day = next_month - timedelta(days=1)
    days_remaining = (last_day - today).days
    
    # Determine status
    if days_remaining <= 0:
        status = "overdue"
    elif days_remaining <= 3:
        status = "due_soon"
    else:
        status = "upcoming"
    
    return {
        "days": days_remaining,
        "deadline_date": last_day.isoformat(),
        "status": status,
    }


def get_entity_stats(user: "User", entity_id: str | None = None) -> Dict[str, Any]:
    """Get entity-scoped statistics."""
    from apps.operations.models import Dog, Vaccination
    from apps.breeding.models import Litter
    from apps.sales.models import SalesAgreement
    
    # Apply entity scoping
    if user.role != "management" and user.entity_id:
        entity_id = str(user.entity_id)
    
    # Base dog queryset
    dogs = Dog.objects.filter(status=Dog.Status.ACTIVE)
    if entity_id:
        dogs = dogs.filter(entity_id=entity_id)
    
    # Total dogs
    total_dogs = dogs.count()
    
    # Active litters (puppies < 8 weeks)
    eight_weeks_ago = date.today() - timedelta(days=56)
    active_litters = Litter.objects.filter(
        whelp_date__gte=eight_weeks_ago
    )
    if entity_id:
        active_litters = active_litters.filter(
            breeding_record__entity_id=entity_id
        )
    
    from apps.sales.models import AgreementStatus
    
    # Pending agreements
    pending_agreements = SalesAgreement.objects.filter(
        status__in=[AgreementStatus.DRAFT, AgreementStatus.SIGNED]
    )
    if entity_id:
        pending_agreements = pending_agreements.filter(entity_id=entity_id)
    
    # Overdue vaccinations
    overdue_vaccinations = Vaccination.objects.filter(
        status=Vaccination.Status.OVERDUE
    )
    if entity_id:
        overdue_vaccinations = overdue_vaccinations.filter(
            dog__entity_id=entity_id
        )
    
    return {
        "total_dogs": total_dogs,
        "active_litters": active_litters.count(),
        "pending_agreements": pending_agreements.count(),
        "overdue_vaccinations": overdue_vaccinations.count(),
    }


def get_recent_activity(user: "User", limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent audit log activity."""
    from apps.core.models import AuditLog
    
    # Entity scoping for activity
    queryset = AuditLog.objects.all().order_by("-created_at")
    
    if user.role != "management" and user.entity_id:
        queryset = queryset.filter(
            Q(payload__entity_id=str(user.entity_id)) |
            Q(actor__entity_id=user.entity_id)
        )
    
    logs = queryset[:limit]
    
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "actor_name": log.actor.get_full_name() if log.actor else "System",
            "timestamp": log.created_at.isoformat(),
        }
        for log in logs
    ]


def get_revenue_summary(user: "User", months: int = 6) -> Dict[str, Any] | None:
    """Get revenue summary for last N months.
    
    Only available for Management and Admin roles.
    """
    if user.role not in ["management", "admin", "sales"]:
        return None
    
    from apps.sales.models import SalesAgreement, AgreementStatus
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=30 * months)
    
    # Base queryset
    agreements = SalesAgreement.objects.filter(
        status=AgreementStatus.COMPLETED,
        signed_at__gte=start_date,
        signed_at__lte=end_date,
    )
    
    # Entity scoping
    if user.role != "management" and user.entity_id:
        agreements = agreements.filter(entity_id=user.entity_id)
    
    # Monthly aggregation
    monthly_data = []
    current = start_date
    
    for _ in range(months):
        month_end = (current.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_agreements = agreements.filter(
            signed_at__gte=current,
            signed_at__lte=month_end
        )
        
        total_sales = month_agreements.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        # Calculate GST (price * 9 / 109)
        gst_collected = total_sales * Decimal('9') / Decimal('109')
        
        monthly_data.append({
            "month": current.strftime("%Y-%m"),
            "month_label": current.strftime("%b %Y"),
            "total_sales": float(total_sales),
            "gst_collected": float(gst_collected),
        })
        
        current = month_end + timedelta(days=1)
        if current > end_date:
            break
    
    # Totals
    total_revenue = sum(m["total_sales"] for m in monthly_data)
    total_gst = sum(m["gst_collected"] for m in monthly_data)
    
    return {
        "period_months": months,
        "monthly_data": monthly_data,
        "total_revenue": total_revenue,
        "total_gst": total_gst,
    }


def get_dashboard_metrics(user: "User") -> Dict[str, Any]:
    """Get complete dashboard metrics for a user.
    
    Implements role-aware payload construction per Phase 8 requirements.
    """
    # Entity scoping
    entity_id = None
    if user.role != "management" and user.entity_id:
        entity_id = str(user.entity_id)
    
    # Stats
    stats = get_entity_stats(user, entity_id)
    
    # Alerts (from existing service)
    from apps.operations.services.alerts import get_all_alert_cards
    alerts = get_all_alert_cards(user, entity_id)
    
    # NParks countdown
    nparks_countdown = get_nparks_countdown()
    
    # Recent activity
    recent_activity = get_recent_activity(user)
    
    # Build base response
    response = {
        "role": user.role,
        "entity_id": entity_id,
        "stats": stats,
        "alerts": alerts,
        "nparks_countdown": nparks_countdown,
        "recent_activity": recent_activity,
    }
    
    # Role-specific additions
    if user.role in ["management", "admin", "sales"]:
        response["revenue_summary"] = get_revenue_summary(user)
    
    if user.role in ["vet", "admin", "management"]:
        # Vet sees health-focused metrics
        from apps.operations.services.alerts import get_vaccine_overdue, get_nursing_flags
        response["health_alerts"] = {
            "overdue_vaccines": len(get_vaccine_overdue(entity_id)),
            "nursing_flags": len(get_nursing_flags(entity_id)),
        }
    
    if user.role in ["sales", "admin", "management"]:
        # Sales sees pipeline metrics
        from apps.sales.models import SalesAgreement, AgreementStatus
        pipeline = SalesAgreement.objects.filter(
            status__in=[AgreementStatus.DRAFT, AgreementStatus.SIGNED]
        )
        if entity_id:
            pipeline = pipeline.filter(entity_id=entity_id)
        
        response["sales_pipeline"] = {
            "draft_count": pipeline.filter(status=AgreementStatus.DRAFT).count(),
            "signed_count": pipeline.filter(status=AgreementStatus.SIGNED).count(),
        }
    
    return response


def get_cached_dashboard_metrics(user: "User") -> Dict[str, Any]:
    """Get dashboard metrics with caching."""
    cache_key = f"dashboard_metrics:{user.id}:{user.role}:{user.entity_id or 'all'}"
    
    # Try cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Generate fresh metrics
    metrics = get_dashboard_metrics(user)
    
    # Cache for 60 seconds
    cache.set(cache_key, metrics, CACHE_TTL)
    
    return metrics
