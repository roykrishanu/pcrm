"""Celery app for background jobs (section 49): email sending, CSV import/
export, webhook delivery, reminder processing, report generation. Add task
modules under app/workers/tasks/ and import them here as they're built."""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "crm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")


@celery_app.task(name="ping")
def ping() -> str:
    return "pong"
