from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "lifeos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    # Dev / tests: run tasks in-process, no broker or worker required.
    task_always_eager=settings.celery_eager,
    task_eager_propagates=True,
    task_track_started=True,
    timezone="UTC",
    beat_schedule={
        "due-reminders": {
            "task": "app.worker.tasks.dispatch_due_reminders",
            "schedule": 60.0,
        },
        "daily-digest": {
            "task": "app.worker.tasks.send_daily_digest",
            "schedule": crontab(hour=7, minute=0),
        },
    },
)
