"""
Reset all ad data and re-collect from Meta Ad Library with specific filters.

Usage:
  python -m scripts.reset_and_collect [--keep-users]

Filters applied (matching Meta Ad Library UI):
  - Platform: Facebook
  - Active status: ACTIVE
  - Impressions by date: >= 2026-03-01
  - Media type: VIDEO
"""
import argparse
import asyncio
import logging
import sys

from sqlalchemy import text

from app.core.database import async_session, engine
from app.search.es_client import es_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("reset_and_collect")


async def clear_ads_data(keep_users: bool = True):
    """Delete all ad-related data from PostgreSQL."""
    async with async_session() as db:
        # Order matters — FK constraints
        tables_to_clear = [
            "ad_analyses",
            "board_items",
            "competitor_alerts",
            "ads",
        ]
        for table in tables_to_clear:
            try:
                result = await db.execute(text(f"DELETE FROM {table}"))
                logger.info(f"  Cleared {table}: {result.rowcount} rows")
            except Exception as e:
                logger.warning(f"  Skip {table}: {e}")
        await db.commit()
    logger.info("PostgreSQL ad data cleared.")


async def clear_elasticsearch():
    """Delete and recreate the ads ES index (skip if ES unavailable)."""
    try:
        await es_client.initialize()
        es = es_client.client
    except Exception:
        logger.info("Elasticsearch unavailable, skipping clear.")
        return

    try:
        index = "ads"
        if await es.indices.exists(index=index):
            await es.delete_by_query(
                index=index,
                body={"query": {"match_all": {}}},
                refresh=True,
            )
            logger.info("Elasticsearch 'ads' index cleared.")
        else:
            logger.info("Elasticsearch 'ads' index does not exist, skipping.")
    finally:
        await es_client.close()


async def collect_meta_videos():
    """Collect active Facebook video ads with impressions >= 2026-03-01."""
    from app.collectors.meta_collector import collect_and_store

    logger.info("Starting Meta collection with filters:")
    logger.info("  ad_active_status = ACTIVE")
    logger.info("  ad_delivery_date_min = 2026-03-01")
    logger.info("  media_type = VIDEO")
    logger.info("  countries = VN")

    stats = await collect_and_store(
        ad_active_status="ACTIVE",
        ad_delivery_date_min="2026-03-01",
        media_type="VIDEO",
        countries=["VN"],
        limit=100,
        max_pages=5,
    )
    return stats


async def run_lifecycle():
    """Run hot-ads scoring and deduplication after collection."""
    from app.services.lifecycle import update_hot_ads, dedupe_ads

    async with async_session() as db:
        hot = await update_hot_ads(db)
        logger.info(f"Hot ads updated: {hot}")
        deduped = await dedupe_ads(db)
        logger.info(f"Deduplication done: {deduped}")


async def main(keep_users: bool = True):
    logger.info("=" * 60)
    logger.info("RESET & RE-COLLECT")
    logger.info("=" * 60)

    # Step 1: Clear data
    logger.info("\n[1/4] Clearing PostgreSQL ad data...")
    await clear_ads_data(keep_users=keep_users)

    # Step 2: Clear ES
    logger.info("\n[2/4] Clearing Elasticsearch...")
    await clear_elasticsearch()

    # Step 3: Collect
    logger.info("\n[3/4] Collecting from Meta Ad Library...")
    stats = await collect_meta_videos()
    logger.info(f"Collection stats: {stats}")

    # Step 4: Lifecycle
    logger.info("\n[4/4] Running lifecycle tasks (scoring + dedupe)...")
    await run_lifecycle()

    logger.info("\n" + "=" * 60)
    logger.info("DONE!")
    logger.info(f"  Fetched: {stats['fetched']}")
    logger.info(f"  New:     {stats['new']}")
    logger.info(f"  Updated: {stats['updated']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset ad data and re-collect")
    parser.add_argument("--keep-users", action="store_true", default=True,
                        help="Keep user accounts (default: True)")
    args = parser.parse_args()
    asyncio.run(main(keep_users=args.keep_users))
