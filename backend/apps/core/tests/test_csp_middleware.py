"""
TDD: CSP Middleware Activation
==============================
Phase 1 — Ensure Content-Security-Policy header is emitted.

Currently: django-csp is installed but not in INSTALLED_APPS or MIDDLEWARE,
so CSP settings are inert and no headers are emitted.

CSP uses Report-Only mode in development (CSP_REPORT_ONLY=True),
so the header is Content-Security-Policy-Report-Only.
"""

from django.test import Client, override_settings


def test_csp_header_present_on_health_response():
    """Verify CSP header is emitted — checks both enforce and report-only."""
    client = Client(SERVER_NAME="localhost")
    response = client.get("/health/")
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    csp_header = (
        response.headers.get("Content-Security-Policy")
        or response.headers.get("Content-Security-Policy-Report-Only")
        or ""
    )
    assert csp_header, (
        "CSP header missing — django-csp middleware is not configured. "
        f"Headers present: {dict(response.headers)}"
    )


def test_csp_default_src_self():
    client = Client(SERVER_NAME="localhost")
    response = client.get("/health/")
    csp = (
        response.headers.get("Content-Security-Policy")
        or response.headers.get("Content-Security-Policy-Report-Only")
        or ""
    )
    assert "default-src 'self'" in csp


def test_csp_script_src_self():
    client = Client(SERVER_NAME="localhost")
    response = client.get("/health/")
    csp = (
        response.headers.get("Content-Security-Policy")
        or response.headers.get("Content-Security-Policy-Report-Only")
        or ""
    )
    assert "script-src 'self'" in csp