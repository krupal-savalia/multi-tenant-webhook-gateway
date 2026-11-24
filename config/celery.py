from celery import Celery
import os

os.environ.setdefault(
     "DJANGO_SETTINGS_MODULE", "config.settings.local",
)

app = Celery("webhook_gateway")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

app.autodiscover_tasks()