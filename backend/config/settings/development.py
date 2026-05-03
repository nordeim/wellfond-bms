"""Development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True

# Direct to PostgreSQL (not PgBouncer) for dev
DATABASES["default"]["HOST"] = os.environ.get("POSTGRES_HOST", "localhost")  # noqa: F405
DATABASES["default"]["PORT"] = os.environ.get("POSTGRES_PORT", "5432")
DATABASES["default"]["USER"] = os.environ.get("POSTGRES_USER", "wellfond_user")
DATABASES["default"]["NAME"] = os.environ.get("POSTGRES_DB", "wellfond_db")

# Relaxed CSP for dev — report-only mode, wider script-src for HMR
CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "font-src": ["'self'"],
    }
}
CONTENT_SECURITY_POLICY = {}  # No enforced policy in dev

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
