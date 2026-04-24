# This will be populated by celery.py once it's created
from .celery import app as celery_app

__all__ = ("celery_app",)
