"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for Docker and load balancers."""
    return JsonResponse({"status": "ok", "service": "wellfond-bms"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/v1/", include("api.urls")),
]
