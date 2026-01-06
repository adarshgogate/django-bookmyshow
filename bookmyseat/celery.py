import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookmyseat.settings")

app = Celery("bookmyseat")

app.conf.broker_url = "redis://localhost:6379/0"
app.conf.result_backend = "redis://localhost:6379/0"

# Load settings with CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all apps
app.autodiscover_tasks()
