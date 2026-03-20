from typing import cast, Any

from celery import Celery
from celery.schedules import crontab

from src.config.settings import get_settings

# Celery main settings

settings = get_settings()

celery_instance = Celery(
    "auction_worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "src.tasks.auction_tasks",
        "src.tasks.token_tasks",
    ],
)

celery_instance.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kyiv",
    enable_utc=True,
)

celery_instance.conf.beat_schedule = {
    "clear-expired-refresh-tokens-every-hour": {
        "task": "remove_expired_refresh_tokens_task",
        "schedule": cast(Any, crontab(minute="30")),
    },
}
