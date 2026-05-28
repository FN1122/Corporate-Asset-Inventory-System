"""
Celery application for CAIMS.

This sets up the Celery instance, tells it to read configuration from
Django settings (the CELERY_* values), and auto-discovers tasks.py files
in the installed apps.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caims.settings")

app = Celery("caims")

# Read any setting prefixed with CELERY_ from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Find tasks.py in each installed app automatically.
app.autodiscover_tasks()
