"""Ad data lifecycle management — async logic.

Pure async functions, no Celery dependency. Called by tasks/lifecycle_tasks.py.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad

logger = logging.getLogger(__name__)


async def mark_expired_ads(db: AsyncSession, expire_days: int = 7) -> dict:
    """Mark ads as inactive if not seen for `expire_days`."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=expire_days)
    result = await db.execute(
        update(Ad)
        .where(Ad.is_active.is_(True))
        .where(Ad.last_seen < cutoff)
        .values(is_active=False)
    )
    count = result.rowcount
    await db.commit()
    logger.info(f"[lifecycle] Marked {count} ads as expired (last_seen < {cutoff.date()})")
    return {"expired": count}


async def update_hot_ads(db: AsyncSession, hot_threshold: float = 50.0) -> dict:
    """Recalculate viral_score for active ads and set is_hot flag."""
    result = await db.execute(
        select(Ad).where(Ad.is_active.is_(True), Ad.likes.isnot(None))
    )
    ads = result.scalars().all()

    updated = 0
    for ad in ads:
        likes = ad.likes or 0
        comments = ad.comments or 0
        shares = ad.shares or 0
        total_engagement = likes + comments * 2 + shares * 3

        # Recency boost: decay 5% per day
        recency = 1.0
        if ad.last_seen:
            last_seen = ad.last_seen
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            days_ago = (datetime.now(timezone.utc) - last_seen).days
            recency = max(0.2, 1.0 - (days_ago * 0.05))

        score = min(100.0, (total_engagement / 100.0) * recency)

        engagement_rate = None
        impressions = ad.impressions_upper or ad.impressions_lower
        if impressions and impressions > 0:
            engagement_rate = (total_engagement / impressions) * 100

        new_is_hot = score >= hot_threshold

        if ad.viral_score != score or ad.is_hot != new_is_hot:
            ad.viral_score = round(score, 2)
            ad.is_hot = new_is_hot
            if engagement_rate is not None:
                ad.engagement_rate = round(engagement_rate, 2)
            updated += 1

    await db.commit()
    logger.info(f"[lifecycle] Updated viral_score for {updated} ads")
    return {"updated": updated}


async def archive_stale_ads(db: AsyncSession, es, index_name: str,
                            stale_days: int = 30, batch_size: int = 500) -> dict:
    """Remove inactive old ads from ES index (keep in DB)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
    result = await db.execute(
        select(Ad.id).where(
            Ad.is_active.is_(False),
            Ad.last_seen < cutoff,
        ).limit(batch_size)
    )
    ad_ids = [str(row[0]) for row in result.all()]

    if not ad_ids:
        logger.info("[lifecycle] No stale ads to archive from ES")
        return {"archived": 0}

    try:
        body = [
            {"delete": {"_index": index_name, "_id": ad_id}}
            for ad_id in ad_ids
        ]
        await es.bulk(operations=body, refresh=True)
        logger.info(f"[lifecycle] Archived {len(ad_ids)} stale ads from ES index")
    except Exception as e:
        logger.error(f"[lifecycle] Failed to archive from ES: {e}")
        return {"archived": 0, "error": str(e)}

    return {"archived": len(ad_ids)}


async def dedupe_ads(db: AsyncSession) -> dict:
    """Merge ads with the same creative_phash on the same platform."""
    dupe_query = (
        select(Ad.platform, Ad.creative_phash, func.count(Ad.id).label("cnt"))
        .where(Ad.creative_phash.isnot(None), Ad.creative_phash != "")
        .group_by(Ad.platform, Ad.creative_phash)
        .having(func.count(Ad.id) > 1)
    )
    dupes = (await db.execute(dupe_query)).all()

    merged = 0
    for platform, phash, _count in dupes:
        result = await db.execute(
            select(Ad)
            .where(Ad.platform == platform, Ad.creative_phash == phash)
            .order_by(Ad.last_seen.desc().nullslast())
        )
        ads = result.scalars().all()
        keeper = ads[0]

        for dupe in ads[1:]:
            keeper.likes = max(keeper.likes or 0, dupe.likes or 0)
            keeper.comments = max(keeper.comments or 0, dupe.comments or 0)
            keeper.shares = max(keeper.shares or 0, dupe.shares or 0)
            if dupe.first_seen and (not keeper.first_seen or dupe.first_seen < keeper.first_seen):
                keeper.first_seen = dupe.first_seen
            dupe.is_active = False
            merged += 1

    await db.commit()
    logger.info(f"[lifecycle] Deduped {merged} duplicate ads")
    return {"merged": merged}


async def cleanup_incomplete(db: AsyncSession) -> dict:
    """Mark ads missing headline + body + media as inactive."""
    result = await db.execute(
        update(Ad)
        .where(
            Ad.is_active.is_(True),
            Ad.headline.is_(None),
            Ad.body_text.is_(None),
            or_(
                Ad.media_urls.is_(None),
                Ad.media_urls == "[]",
                Ad.media_urls == "null",
            ),
        )
        .values(is_active=False)
    )
    count = result.rowcount
    await db.commit()
    logger.info(f"[lifecycle] Marked {count} incomplete ads as inactive")
    return {"cleaned": count}


async def purge_old_ads(db: AsyncSession, purge_days: int = 30,
                        batch_size: int = 1000) -> dict:
    """Permanently delete inactive ads older than `purge_days` not saved in any board."""
    from app.models.board_ad import BoardAd

    cutoff = datetime.now(timezone.utc) - timedelta(days=purge_days)
    saved_ids_query = select(BoardAd.ad_id).distinct()

    to_purge_query = (
        select(Ad.id)
        .where(
            Ad.is_active.is_(False),
            Ad.last_seen < cutoff,
            ~Ad.id.in_(saved_ids_query),
        )
        .limit(batch_size)
    )
    result = await db.execute(to_purge_query)
    ids_to_purge = [row[0] for row in result.all()]

    if not ids_to_purge:
        logger.info("[lifecycle] No old ads to purge")
        return {"purged": 0}

    await db.execute(delete(Ad).where(Ad.id.in_(ids_to_purge)))
    await db.commit()
    logger.info(f"[lifecycle] Purged {len(ids_to_purge)} old ads permanently")
    return {"purged": len(ids_to_purge)}
