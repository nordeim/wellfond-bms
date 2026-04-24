"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Direct to PostgreSQL (not PgBouncer) for dev
DATABASES["default"]["HOST"] = os.environ.get("POSTGRES_HOST", "localhost")  # noqa: F405
DATABASES["default"]["PORT"] = os.environ.get("POSTGRES_PORT", "5432")

# Relaxed CSP for dev
SECURE_CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")  # noqa: F405
SECURE_CSP_REPORT_ONLY = True  # noqa: F405

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# CORS — allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Email — console backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
