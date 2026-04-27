"""API package — Wellfond BMS."""

from ninja import NinjaAPI
from ninja.errors import ValidationError
from django.http import JsonResponse

api = NinjaAPI(
    title="Wellfond BMS",
    version="1.0.0",
    urls_namespace="api",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs/",
)


@api.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    return JsonResponse(
        {"error": "Validation error", "details": exc.errors},
        status=422,
    )


@api.exception_handler(Exception)
def generic_error_handler(request, exc):
    return JsonResponse(
        {"error": "Internal server error"},
        status=500,
    )


# -------------------------------------------------------------------------
# Router Registration
# -------------------------------------------------------------------------
from apps.core.routers import auth_router, users_router

# Core routers
api.add_router("/auth", auth_router, tags=["auth"])
api.add_router("/users", users_router, tags=["users"])

# Domain routers
from apps.operations.routers import (
    alerts_router,
    dogs_router,
    health_router,
    logs_router,
    stream_router,
)

api.add_router("/alerts", alerts_router, tags=["alerts"])
api.add_router("/dogs", dogs_router, tags=["dogs"])
api.add_router("/health", health_router, tags=["health"])
api.add_router("/ground-logs", logs_router, tags=["ground-logs"])
api.add_router("/stream", stream_router, tags=["sse-stream"])

# Breeding & Genetics routers (Phase 4)
from apps.breeding.routers import mating_router, litters_router

api.add_router("/breeding/mate-check", mating_router, tags=["breeding"])
api.add_router("/breeding", litters_router, tags=["breeding"])

# Additional routers will be registered here as apps are built:
# api.add_router("/sales", sales_router, tags=["sales"])
# api.add_router("/compliance", compliance_router, tags=["compliance"])
# api.add_router("/customers", customers_router, tags=["customers"])
# api.add_router("/finance", finance_router, tags=["finance"])
