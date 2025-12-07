import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "document_search_engine.settings")

app = Celery("document_search_engine")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
print("Tasks Discovered")