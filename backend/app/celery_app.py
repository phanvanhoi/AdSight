from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "adsight",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Beat schedule — data collection
celery.conf.beat_schedule = {
    "collect-meta-ads-every-2h": {
        "task": "app.tasks.collection_tasks.collect_meta_ads",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "collect-tiktok-ads-every-4h": {
        "task": "app.tasks.collection_tasks.collect_tiktok_ads",
        "schedule": crontab(minute=30, hour="*/4"),
    },
}

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])
