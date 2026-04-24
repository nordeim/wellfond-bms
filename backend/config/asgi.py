"""ASGI config for Wellfond BMS — supports async views and SSE."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
