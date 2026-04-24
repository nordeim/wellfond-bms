"""Production settings."""
from .base import *  # noqa: F401,F403

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

# Session cookies — secure in production
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Strict CSP (no unsafe-eval)
SECURE_CSP_SCRIPT_SRC = ("'self'",)  # noqa: F405
SECURE_CSP_REPORT_ONLY = False  # noqa: F405
