"""
Wellfond BMS - URL Configuration
================================
Root URL configuration with health checks and API mounting.
"""

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

from api import api


def health_check(request):
    """
    Health check endpoint for load balancers and monitoring.
    Returns: {"status": "ok", "service": "wellfond-api"}
    """
    return JsonResponse({"status": "ok", "service": "wellfond-api", "version": "1.0.0"})


def ready_check(request):
    """
    Readiness check - verifies database connectivity.
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception as e:
        return JsonResponse({"status": "not_ready", "error": str(e)}, status=503)


# -----------------------------------------------------------------------------
# URL Patterns
# -----------------------------------------------------------------------------
urlpatterns = [
    # Health checks
    path("health/", health_check, name="health"),
    path("ready/", ready_check, name="ready"),
    # Django Admin
    path("admin/", admin.site.urls),
    # Ninja API v1
    path("api/v1/", api.urls),
]
