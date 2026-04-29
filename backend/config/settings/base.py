"""
Django settings — Wellfond BMS (base)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django defaults
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "corsheaders",
    "django_celery_beat",
    # Domain apps — implemented
    "apps.core",
    "apps.operations",
    "apps.breeding",
    "apps.sales",  # Phase 5: Sales Agreements & AVS
    "apps.compliance",  # Phase 6: Compliance & NParks Reporting
    "apps.customers",  # Phase 7: Customer DB & Marketing Blast
    # Phase 8: Finance & Dashboard
    "apps.finance",
    # Domain apps — to be added in future phases:
    # Phase 9: "apps.ai_sandbox",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "apps.core.middleware.AuthenticationMiddleware",  # Custom Redis-based auth (sets request.user)
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django admin support
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.IdempotencyMiddleware",
    "apps.core.middleware.EntityScopingMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",  # Rate limit exception handling
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — PgBouncer transaction pooling
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "wellfond"),
        "USER": os.environ.get("POSTGRES_USER", "wellfond_app"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD")
        or os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST", "pgbouncer"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,  # Mandatory for PgBouncer transaction mode
        "OPTIONS": {
            "sslmode": "prefer",
        },
    }
}

# ---------------------------------------------------------------------------
# Redis — Split instances
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://redis_cache:6379/0"),
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get(
            "REDIS_SESSIONS_URL", "redis://redis_sessions:6379/0"
        ),
    },
    "idempotency": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://redis_cache:6379/0"),
    },
}

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days

# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Celery — Native configuration (no django.tasks bridge)
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_BROKER_URL", "redis://redis_broker:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_CACHE_URL", "redis://redis_cache:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Asia/Singapore"
CELERY_TASK_ROUTES = {
    "apps.compliance.*": {"queue": "high"},
    "apps.sales.tasks.*": {"queue": "default"},
    "apps.breeding.tasks.*": {"queue": "low"},
    "apps.customers.tasks.*": {"queue": "default"},
    "apps.operations.tasks.*": {"queue": "low"},
}
CELERY_BEAT_SCHEDULE = {
    "avs-reminder-check": {
        "task": "apps.sales.tasks.avs_reminder_check",
        "schedule": 60 * 60 * 24,  # Daily
    },
    "check-overdue-vaccines": {
        "task": "apps.operations.tasks.check_overdue_vaccines",
        "schedule": 60 * 60 * 24,  # Daily
    },
    "check-rehome-overdue": {
        "task": "apps.operations.tasks.check_rehome_overdue",
        "schedule": 60 * 60 * 24,  # Daily
    },
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Custom User model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "core.User"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-sg"
TIME_ZONE = "Asia/Singapore"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# Media files
# ---------------------------------------------------------------------------
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Content Security Policy
# ---------------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # Tailwind JIT requires inline
CSP_IMG_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FONT_SRC = ("'self'",)
CSP_REPORT_ONLY = False

# ---------------------------------------------------------------------------
# Logging — Structured JSON
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if not DEBUG else "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Gotenberg
# ---------------------------------------------------------------------------
GOTENBERG_URL = os.environ.get("GOTENBERG_URL", "http://gotenberg:3000")

# ---------------------------------------------------------------------------
# Ninja API
# ---------------------------------------------------------------------------
NINJA_PAGINATION_CLASS = "ninja.pagination.PageNumberPagination"
NINJA_PAGINATION_PER_PAGE = 25

# ---------------------------------------------------------------------------
# Rate Limiting (django-ratelimit)
# ---------------------------------------------------------------------------
RATELIMIT_VIEW = "apps.core.routers.auth.ratelimit_handler"
