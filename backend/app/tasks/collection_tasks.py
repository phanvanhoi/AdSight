import asyncio
import logging

from app.celery_app import celery
from app.collectors.meta_collector import MetaCollector, VN_SEARCH_TERMS
from app.collectors.tiktok_collector import TikTokCollector
from app.collectors.pipeline import process_ads
from app.core.database import async_session
from app.search.es_client import es_client

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _collect_meta():
    collector = MetaCollector()
    await es_client.initialize()
    es = es_client.client

    total_new = 0
    for term in VN_SEARCH_TERMS:
        try:
            ads = await collector.collect_with_retry({
                "search_terms": term,
                "ad_reached_countries": ["VN"],
                "limit": 100,
                "max_pages": 3,
            })
            if ads:
                async with async_session() as db:
                    new_count = await process_ads(db, es, ads)
                    total_new += new_count
                    logger.info(f"[meta] '{term}': {new_count} new ads")
        except Exception as e:
            logger.error(f"[meta] Error collecting '{term}': {e}")

    await es_client.close()
    return total_new


async def _collect_tiktok():
    collector = TikTokCollector()
    await es_client.initialize()
    es = es_client.client

    try:
        ads = await collector.collect_with_retry({
            "country_code": "VN",
            "period": 30,
            "limit": 50,
            "max_pages": 5,
        })
        if ads:
            async with async_session() as db:
                new_count = await process_ads(db, es, ads)
                logger.info(f"[tiktok] {new_count} new ads")
                return new_count
    except Exception as e:
        logger.error(f"[tiktok] Error: {e}")
    finally:
        await es_client.close()

    return 0


@celery.task(name="app.tasks.collection_tasks.collect_meta_ads")
def collect_meta_ads():
    """Scheduled task: collect ads from Meta Ad Library."""
    logger.info("Starting Meta ads collection...")
    total = run_async(_collect_meta())
    logger.info(f"Meta collection complete. {total} new ads.")
    return total


@celery.task(name="app.tasks.collection_tasks.collect_tiktok_ads")
def collect_tiktok_ads():
    """Scheduled task: collect ads from TikTok Creative Center."""
    logger.info("Starting TikTok ads collection...")
    total = run_async(_collect_tiktok())
    logger.info(f"TikTok collection complete. {total} new ads.")
    return total
