from celery import Celery

from common.config import get_settings

settings = get_settings()

celery_app = Celery(
    "helmet_violation_detection",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
)
