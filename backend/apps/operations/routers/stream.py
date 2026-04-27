"""
SSE Stream Router for Real-time Alerts
======================================
Reconnect-safe Server-Sent Events with entity scoping.
"""

import asyncio
import json
from typing import AsyncGenerator
from uuid import UUID

from asgiref.sync import sync_to_async
from django.http import StreamingHttpResponse
from ninja import Router

from apps.core.auth import get_authenticated_user
from apps.core.permissions import scope_entity
from apps.operations.models import Dog
from ..services.alerts import get_pending_alerts

router = Router(tags=["sse-stream"])

# SSE poll interval (seconds)
POLL_INTERVAL = 5
# SSE reconnect delay (seconds)
RECONNECT_DELAY = 3


async def _generate_alert_stream(
    user_id: str,
    entity_id: str,
    user_role: str,
) -> AsyncGenerator[str, None]:
    """
    Async generator for SSE events.

    Yields:
        Formatted SSE event strings with alert data.
    """
    import time

    # Track last event ID for deduplication
    last_event_id = 0

    while True:
        try:
            # Get pending alerts using sync_to_async for proper thread handling
            alerts = await sync_to_async(get_pending_alerts, thread_sensitive=True)(
                user_id=user_id,
                entity_id=entity_id,
                role=user_role,
                since_id=last_event_id,
            )

            if alerts:
                for alert in alerts:
                    event_data = {
                        "id": alert["id"],
                        "type": alert["type"],
                        "dog_id": alert["dog_id"],
                        "dog_name": alert["dog_name"],
                        "message": alert["message"],
                        "severity": alert.get("severity", "info"),
                        "created_at": alert["created_at"],
                    }

                    # Format SSE event
                    yield f"id: {alert['id']}\n"
                    yield f"event: {alert['type']}\n"
                    yield f"data: {json.dumps(event_data)}\n\n"

                    last_event_id = max(last_event_id, alert["id"])

            # Send heartbeat to keep connection alive
            yield f": heartbeat\n\n"

            # Wait for next poll
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            # Log error and keep connection alive
            error_data = {"error": str(e), "reconnect_delay": RECONNECT_DELAY}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
            await asyncio.sleep(RECONNECT_DELAY)


@router.get("/alerts")
def alert_stream(request):
    """
    SSE endpoint for real-time alert streaming.

    Returns a Server-Sent Events stream with:
    - New alerts for user's entity
    - Heartbeat every 5 seconds
    - Automatic reconnection support

    Connection headers:
    - Accept: text/event-stream
    - Cache-Control: no-cache
    - Connection: keep-alive
    """
    user = get_authenticated_user(request)

    if not user:
        from django.http import JsonResponse

        return JsonResponse(
            {"error": "Authentication required"},
            status=401,
        )

    # Get user info for entity scoping
    user_id = str(user.id)
    entity_id = str(user.entity_id) if user.entity_id else None
    user_role = user.role

    # For management, they can see all entities
    # For others, scope to their entity
    if user_role != "management" and not entity_id:
        from django.http import JsonResponse

        return JsonResponse(
            {"error": "User not assigned to an entity"},
            status=403,
        )

    response = StreamingHttpResponse(
        streaming_content=_generate_alert_stream(
            user_id=user_id,
            entity_id=entity_id,
            user_role=user_role,
        ),
        content_type="text/event-stream",
    )

    # SSE headers for proper streaming
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering

    return response


# =============================================================================
# Dog-specific SSE Streams
# =============================================================================


async def _generate_dog_alert_stream(
    dog_id: str,
    user_id: str,
    entity_id: str,
    user_role: str,
) -> AsyncGenerator[str, None]:
    """
    Async generator for dog-specific SSE events.
    """
    import time

    last_event_id = 0

    while True:
        try:
            # Get pending alerts for specific dog
            alerts = await asyncio.to_thread(
                get_pending_alerts,
                user_id=user_id,
                entity_id=entity_id,
                role=user_role,
                since_id=last_event_id,
                dog_id=dog_id,
            )

            if alerts:
                for alert in alerts:
                    event_data = {
                        "id": alert["id"],
                        "type": alert["type"],
                        "dog_id": alert["dog_id"],
                        "dog_name": alert["dog_name"],
                        "message": alert["message"],
                        "severity": alert.get("severity", "info"),
                        "created_at": alert["created_at"],
                    }

                    yield f"id: {alert['id']}\n"
                    yield f"event: {alert['type']}\n"
                    yield f"data: {json.dumps(event_data)}\n\n"

                    last_event_id = max(last_event_id, alert["id"])

            # Heartbeat
            yield f": heartbeat\n\n"

            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            error_data = {"error": str(e), "reconnect_delay": RECONNECT_DELAY}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
            await asyncio.sleep(RECONNECT_DELAY)


@router.get("/alerts/{dog_id}")
def dog_alert_stream(request, dog_id: UUID):
    """
    SSE endpoint for dog-specific real-time alerts.
    """
    user = get_authenticated_user(request)

    if not user:
        from django.http import JsonResponse

        return JsonResponse(
            {"error": "Authentication required"},
            status=401,
        )

    # Verify dog access
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        from django.http import JsonResponse

        return JsonResponse(
            {"error": "Dog not found"},
            status=404,
        )

    # Check entity permission
    if user.role != "management" and str(dog.entity_id) != str(user.entity_id):
        from django.http import JsonResponse

        return JsonResponse(
            {"error": "Access denied"},
            status=403,
        )

    user_id = str(user.id)
    entity_id = str(user.entity_id) if user.entity_id else None
    user_role = user.role

    response = StreamingHttpResponse(
        streaming_content=_generate_dog_alert_stream(
            dog_id=str(dog_id),
            user_id=user_id,
            entity_id=entity_id,
            user_role=user_role,
        ),
        content_type="text/event-stream",
    )

    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    response["X-Accel-Buffering"] = "no"

    return response
