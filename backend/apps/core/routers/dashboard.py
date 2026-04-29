"""Dashboard Router - Wellfond BMS
===============================
Role-aware dashboard metrics endpoint.

GET /dashboard/metrics - Returns role-specific dashboard data
"""

from ninja import Router
from ninja.errors import HttpError

from apps.core.permissions import scope_entity, require_role
from apps.core.auth import get_authenticated_user
from apps.core.services.dashboard import get_cached_dashboard_metrics, get_dashboard_metrics

router = Router(tags=["dashboard"])


def _get_current_user(request):
    """Get current user from session cookie."""
    return get_authenticated_user(request)


@router.get("/metrics", response=dict)
def get_metrics(request, entity: str = None):
    """
    Get dashboard metrics for the current user.
    
    Returns role-aware dashboard data including:
    - Stats: total_dogs, active_litters, pending_agreements, overdue_vaccinations
    - Alerts: vaccine_overdue, rehome_overdue, in_heat, nursing_flags, etc.
    - NParks countdown: days until submission deadline
    - Recent activity: last 10 audit logs
    - Revenue summary: last 6 months (Management/Admin/Sales only)
    - Health alerts: overdue vaccines, nursing flags (Vet/Admin/Management only)
    - Sales pipeline: draft/signed agreement counts (Sales/Admin/Management only)
    
    Query params:
    - entity: Optional entity filter (management only)
    
    Response cached for 60 seconds per user.
    """
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    # Apply entity override for management
    if entity and user.role == "management":
        pass  # Management can view any entity
    else:
        # Non-management: scope to their entity
        if user.entity_id:
            entity = str(user.entity_id)
    
    # Get cached metrics
    metrics = get_cached_dashboard_metrics(user)
    
    return metrics


@router.get("/activity/stream")
def activity_stream(request):
    """
    SSE endpoint for real-time dashboard activity feed.
    
    Streams audit log events as they occur.
    """
    from django.http import StreamingHttpResponse
    import json
    import asyncio
    import time
    
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    async def event_generator():
        """Generate SSE events."""
        from apps.core.services.dashboard import get_recent_activity
        
        last_check = time.time()
        
        while True:
            # Check for new activity every 5 seconds
            await asyncio.sleep(5)
            
            try:
                activity = get_recent_activity(user, limit=1)
                
                if activity:
                    event_time = activity[0]["timestamp"]
                    # Only send if new since last check
                    if event_time > last_check:
                        yield f"data: {json.dumps(activity[0])}\n\n"
                        last_check = event_time
                
                # Send keepalive
                yield f": keepalive\n\n"
                
            except Exception:
                yield f": error\n\n"
    
    response = StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    
    return response
