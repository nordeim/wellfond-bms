"""Celery app configuration — Wellfond BMS."""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("wellfond")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ---------------------------------------------------------------------------
# Beat schedule
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    "avs-reminder-check": {
        "task": "apps.sales.tasks.check_avs_reminders",
        "schedule": crontab(hour=9, minute=0),  # Daily 9am SGT
    },
    "check-overdue-vaccines": {
        "task": "apps.operations.tasks.check_overdue_vaccines",
        "schedule": crontab(hour=8, minute=0),  # Daily 8am SGT
    },
    "check-rehome-overdue": {
        "task": "apps.operations.tasks.check_rehome_overdue",
        "schedule": crontab(hour=8, minute=5),  # Daily 8:05am SGT
    },
    "lock-expired-submissions": {
        "task": "apps.compliance.tasks.lock_expired_submissions",
        "schedule": crontab(hour=1, minute=0),  # Daily 1am SGT
    },
}
app.conf.timezone = "Asia/Singapore"
