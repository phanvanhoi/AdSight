import logging

from asgiref.sync import async_to_sync

from app.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    name="app.tasks.collection_tasks.collect_meta_ads",
    time_limit=300,
    soft_time_limit=240,
)
def collect_meta_ads():
    """Scheduled task: collect ads from Meta Ad Library. Runs every 2 hours."""
    from app.collectors.meta_collector import collect_and_store

    logger.info("Starting Meta ads collection...")
    result = async_to_sync(collect_and_store)()
    logger.info(f"Meta collection done: {result}")
    return result


@celery.task(
    name="app.tasks.collection_tasks.collect_tiktok_ads",
    time_limit=300,
    soft_time_limit=240,
)
def collect_tiktok_ads():
    """Scheduled task: collect ads from TikTok Creative Center. Runs every 4 hours."""
    from app.collectors.tiktok_collector import collect_and_store

    logger.info("Starting TikTok ads collection...")
    result = async_to_sync(collect_and_store)()
    logger.info(f"TikTok collection done: {result}")
    return result
