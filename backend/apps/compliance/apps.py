"""
Compliance app configuration.
"""

from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compliance"
    verbose_name = "Compliance"

    def ready(self):
        """App ready - import signal handlers."""
        pass
