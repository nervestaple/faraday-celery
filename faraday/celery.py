import os
from celery import Celery

app = Celery("faraday")
app.conf.update(
    task_concurrency=4,  # Use 4 threads for concurrency
    worker_prefetch_multiplier=1  # Prefetch one task at a time
)
app.config_from_object("faraday.celery_settings", namespace="CELERY")
app.autodiscover_tasks()
