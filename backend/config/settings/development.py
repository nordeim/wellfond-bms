"""Development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True

# Direct to PostgreSQL (not PgBouncer) for dev
DATABASES["default"]["HOST"] = os.environ.get("POSTGRES_HOST", "localhost")  # noqa: F405
DATABASES["default"]["PORT"] = os.environ.get("POSTGRES_PORT", "5432")
DATABASES["default"]["USER"] = os.environ.get("POSTGRES_USER", "wellfond_user")
DATABASES["default"]["NAME"] = os.environ.get("POSTGRES_DB", "wellfond_db")

# Relaxed CSP for dev (dict format for django-csp v4)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_REPORT_ONLY = True

# In dev, move enforce policy to report-only so errors don't break the UI
CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "DIRECTIVES": {
        "default-src": CSP_DEFAULT_SRC,
        "script-src": CSP_SCRIPT_SRC,
        "style-src": CSP_STYLE_SRC,
        "img-src": CSP_IMG_SRC,
        "connect-src": CSP_CONNECT_SRC,
        "font-src": CSP_FONT_SRC,
    }
}
CONTENT_SECURITY_POLICY = {}

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# CORS — allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Email — console backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Redis — use local Redis container
CACHES["default"]["LOCATION"] = os.environ.get(
    "REDIS_CACHE_URL", "redis://localhost:6379/0"
)  # noqa: F405
CACHES["sessions"]["LOCATION"] = os.environ.get(
    "REDIS_SESSIONS_URL", "redis://localhost:6379/1"
)  # noqa: F405
CACHES["idempotency"]["LOCATION"] = os.environ.get(
    "REDIS_CACHE_URL", "redis://localhost:6379/2"
)  # noqa: F405
