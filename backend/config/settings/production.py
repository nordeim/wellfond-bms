"""Production settings."""

import sys
from .base import *  # noqa: F401,F403

# ---------------------------------------------------------------------------
# Validate required environment variables
# ---------------------------------------------------------------------------
_REQUIRED_ENV_VARS = [
    "DJANGO_SECRET_KEY",
    "POSTGRES_PASSWORD",
]

_missing = [var for var in _REQUIRED_ENV_VARS if not os.environ.get(var)]  # noqa: F405
if _missing:
    print(f"FATAL: Missing required environment variables: {', '.join(_missing)}")
    sys.exit(1)

DEBUG = False

# Security hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# Session & CSRF cookies — secure flag only over HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ---------------------------------------------------------------------------
# Content Security Policy (django-csp v4 – enforced mode)
# ---------------------------------------------------------------------------
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "'unsafe-inline'"],  # Tailwind JIT requires inline styles
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "font-src": ["'self'"],
    }
}
CONTENT_SECURITY_POLICY_REPORT_ONLY = {}  # No report-only policy; enforcement is active

# ---------------------------------------------------------------------------
# CSRF trusted origins (set via environment variable if needed)
# ---------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if os.environ.get("CSRF_TRUSTED_ORIGINS") else []
