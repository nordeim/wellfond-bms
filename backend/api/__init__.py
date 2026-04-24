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
