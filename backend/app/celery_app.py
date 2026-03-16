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
    "enrich-unenriched-ads-daily": {
        "task": "app.tasks.collection_tasks.enrich_unenriched_ads",
        "schedule": crontab(minute=0, hour=3),  # 3 AM daily
    },
    "collect-google-ads-every-6h": {
        "task": "app.tasks.collection_tasks.collect_google_ads",
        "schedule": crontab(minute=15, hour="*/6"),
    },
    "crawl-landing-pages-every-6h": {
        "task": "app.tasks.collection_tasks.crawl_landing_pages",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "download-creatives-every-4h": {
        "task": "app.tasks.collection_tasks.download_creatives",
        "schedule": crontab(minute=45, hour="*/4"),
    },
    "collect-tiktok-shop-every-6h": {
        "task": "app.tasks.collection_tasks.collect_tiktok_shop",
        "schedule": crontab(minute=30, hour="*/6"),
    },
    "match-advertisers-daily": {
        "task": "app.tasks.collection_tasks.match_advertisers",
        "schedule": crontab(minute=0, hour=4),  # 4 AM daily
    },
}

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])
