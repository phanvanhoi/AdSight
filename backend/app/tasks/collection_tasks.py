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


@celery.task(
    name="app.tasks.collection_tasks.enrich_unenriched_ads",
    time_limit=600,
    soft_time_limit=540,
)
def enrich_unenriched_ads():
    """Scheduled task: enrich ads missing category_l1. Runs daily."""
    from app.core.database import async_session
    from app.enrichment.pipeline import enrich_new_ads

    async def _run():
        async with async_session() as db:
            return await enrich_new_ads(db)

    logger.info("Starting batch enrichment...")
    result = async_to_sync(_run)()
    logger.info(f"Batch enrichment done: {result}")
    return result


@celery.task(
    name="app.tasks.collection_tasks.collect_google_ads",
    time_limit=300,
    soft_time_limit=240,
)
def collect_google_ads():
    """Scheduled task: collect ads from Google Ads Transparency. Runs every 6h."""
    from app.collectors.google_collector import collect_and_store

    logger.info("Starting Google Ads collection...")
    result = async_to_sync(collect_and_store)()
    logger.info(f"Google Ads collection done: {result}")
    return result


@celery.task(
    name="app.tasks.collection_tasks.crawl_landing_pages",
    time_limit=600,
    soft_time_limit=540,
)
def crawl_landing_pages_task():
    """Scheduled task: crawl landing pages. Runs every 6h."""
    from app.core.database import async_session
    from app.enrichment.landing_page import crawl_landing_pages

    async def _run():
        async with async_session() as db:
            return await crawl_landing_pages(db, batch_size=20, max_total=100)

    logger.info("Starting landing page crawl...")
    result = async_to_sync(_run)()
    logger.info(f"Landing page crawl done: {result}")
    return result


@celery.task(
    name="app.tasks.collection_tasks.download_creatives",
    time_limit=600,
    soft_time_limit=540,
)
def download_creatives_task():
    """Scheduled task: download ad creatives. Runs every 4h."""
    from app.core.database import async_session
    from app.enrichment.creative_downloader import download_creatives

    async def _run():
        async with async_session() as db:
            return await download_creatives(db, batch_size=20, max_total=100)

    logger.info("Starting creative download...")
    result = async_to_sync(_run)()
    logger.info(f"Creative download done: {result}")
    return result


@celery.task(
    name="app.tasks.collection_tasks.collect_tiktok_shop",
    time_limit=600,
    soft_time_limit=540,
)
def collect_tiktok_shop():
    """Scheduled task: collect TikTok Shop products. Runs every 6h."""
    from app.collectors.tiktok_shop_crawler import collect_and_store

    logger.info("Starting TikTok Shop collection...")
    result = async_to_sync(collect_and_store)()
    logger.info(f"TikTok Shop collection done: {result}")
    return result


@celery.task(
    name="app.tasks.collection_tasks.match_advertisers",
    time_limit=300,
    soft_time_limit=240,
)
def match_advertisers_task():
    """Scheduled task: match advertisers across platforms. Runs daily."""
    from app.core.database import async_session
    from app.enrichment.advertiser_matching import match_advertisers

    async def _run():
        async with async_session() as db:
            return await match_advertisers(db)

    logger.info("Starting advertiser matching...")
    result = async_to_sync(_run)()
    logger.info(f"Advertiser matching done: {result}")
    return result
