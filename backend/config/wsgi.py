"""WSGI config for Wellfond BMS."""
import os
from django.core.wsgi import get_wsgi_application

# Allow environment variable override, default to development for safety
# In production, set DJANGO_SETTINGS_MODULE=config.settings.production
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
application = get_wsgi_application()
