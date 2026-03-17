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
    "check-expired-subscriptions": {
        "task": "check_expired_subscriptions",
        "schedule": crontab(hour=0, minute=30),  # 00:30 UTC daily
    },
    "check-competitor-ads-every-2h": {
        "task": "check_competitor_ads",
        "schedule": crontab(minute=10, hour="*/2"),
    },
    "send-daily-digest": {
        "task": "send_daily_digest",
        "schedule": crontab(hour=0, minute=0),  # 00:00 UTC = 07:00 VN
    },
    # --- Data lifecycle ---
    "lifecycle-mark-expired-daily": {
        "task": "lifecycle.mark_expired_ads",
        "schedule": crontab(minute=0, hour=5),  # 5 AM UTC daily
    },
    "lifecycle-update-hot-every-2h": {
        "task": "lifecycle.update_hot_ads",
        "schedule": crontab(minute=20, hour="*/2"),
    },
    "lifecycle-archive-stale-weekly": {
        "task": "lifecycle.archive_stale_ads",
        "schedule": crontab(minute=0, hour=6, day_of_week="sunday"),
    },
    "lifecycle-dedupe-daily": {
        "task": "lifecycle.dedupe_ads",
        "schedule": crontab(minute=30, hour=5),  # 5:30 AM UTC daily
    },
    "lifecycle-cleanup-incomplete-daily": {
        "task": "lifecycle.cleanup_incomplete",
        "schedule": crontab(minute=45, hour=5),  # 5:45 AM UTC daily
    },
    "lifecycle-purge-old-weekly": {
        "task": "lifecycle.purge_old_ads",
        "schedule": crontab(minute=30, hour=6, day_of_week="sunday"),
    },
}

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])
