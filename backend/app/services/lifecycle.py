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
    """Recalculate viral_score for active ads using all available signals.

    Signals used (adapts to what each platform provides):
    1. Engagement (TikTok): likes + comments*2 + shares*3
    2. Ad longevity: days running (first_seen → now) — longer = more successful
    3. Collection count: how many times ad reappeared in API = still being served
    4. Impressions/Spend (Meta, when available)
    5. Advertiser saturation: number of active ad variants from same advertiser
    """
    # Pre-compute advertiser saturation: count active ads per advertiser
    sat_query = (
        select(Ad.advertiser_id, func.count(Ad.id).label("ad_count"))
        .where(Ad.is_active.is_(True), Ad.advertiser_id.isnot(None))
        .group_by(Ad.advertiser_id)
    )
    sat_result = await db.execute(sat_query)
    advertiser_ad_counts = {row[0]: row[1] for row in sat_result.all()}

    result = await db.execute(select(Ad).where(Ad.is_active.is_(True)))
    ads = result.scalars().all()

    updated = 0
    for ad in ads:
        # ── Signal 1: Engagement (primarily TikTok) ──
        likes = ad.likes or 0
        comments = ad.comments or 0
        shares = ad.shares or 0
        total_engagement = likes + comments * 2 + shares * 3
        engagement_score = min(40.0, total_engagement / 100.0)  # max 40 points

        # ── Signal 2: Ad longevity (days running) ──
        longevity_score = 0.0
        if ad.first_seen:
            first = ad.first_seen
            if first.tzinfo is None:
                first = first.replace(tzinfo=timezone.utc)
            days_running = max(1, (datetime.now(timezone.utc) - first).days)
            # 1 day=2pts, 7 days=14pts, 14 days=20pts (cap)
            longevity_score = min(20.0, days_running * 2.0)

        # ── Signal 3: Collection frequency ──
        collection_count = ad.collection_count or 1
        # Each re-collection = still being served = 3pts, max 15pts
        collection_score = min(15.0, (collection_count - 1) * 3.0)

        # ── Signal 4: Impressions & Spend (Meta, when available) ──
        spend_score = 0.0
        impressions = ad.impressions_upper or ad.impressions_lower
        spend = ad.spend_upper or ad.spend_lower
        if impressions and impressions > 0:
            # 1K imp = 2pts, 10K = 10pts, max 15pts
            spend_score = min(15.0, (impressions / 1000.0) * 2.0)
        elif spend and spend > 0:
            # Use spend as fallback: 10K VND = 1pt, max 15pts
            spend_score = min(15.0, spend / 10000.0)

        # ── Signal 5: Advertiser saturation ──
        ad_variants = advertiser_ad_counts.get(ad.advertiser_id, 1)
        # Multiple variants = bigger budget: 2 ads=3pts, 5+=10pts max
        saturation_score = min(10.0, (ad_variants - 1) * 3.0)

        # ── Final score ──
        score = min(100.0, engagement_score + longevity_score + collection_score
                    + spend_score + saturation_score)

        # Recency penalty: decay for ads not seen recently
        if ad.last_seen:
            last_seen = ad.last_seen
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            days_since_seen = (datetime.now(timezone.utc) - last_seen).days
            if days_since_seen > 1:
                score *= max(0.3, 1.0 - (days_since_seen * 0.1))

        engagement_rate = None
        if impressions and impressions > 0 and total_engagement > 0:
            engagement_rate = (total_engagement / impressions) * 100

        new_is_hot = score >= hot_threshold

        if ad.viral_score != round(score, 2) or ad.is_hot != new_is_hot:
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
    """Merge duplicate ads on the same platform.

    Deduplication keys (checked in order):
    1. creative_phash — perceptual image hash (when media is downloaded)
    2. content_hash — SHA-256 of headline+body_text (works with Meta/Google data)

    Keeps the newest ad (by last_seen), merges max engagement metrics.
    """
    merged = 0

    # Dedupe by creative_phash
    phash_dupes = (await db.execute(
        select(Ad.platform, Ad.creative_phash, func.count(Ad.id))
        .where(Ad.creative_phash.isnot(None), Ad.creative_phash != "")
        .group_by(Ad.platform, Ad.creative_phash)
        .having(func.count(Ad.id) > 1)
    )).all()

    for platform, phash, _ in phash_dupes:
        merged += await _merge_group(db, Ad.platform == platform, Ad.creative_phash == phash)

    # Dedupe by content_hash (catches Meta/Google text duplicates)
    content_dupes = (await db.execute(
        select(Ad.platform, Ad.content_hash, func.count(Ad.id))
        .where(
            Ad.content_hash.isnot(None), Ad.content_hash != "",
            Ad.is_active.is_(True),
        )
        .group_by(Ad.platform, Ad.content_hash)
        .having(func.count(Ad.id) > 1)
    )).all()

    for platform, chash, _ in content_dupes:
        merged += await _merge_group(db, Ad.platform == platform, Ad.content_hash == chash)

    await db.commit()
    logger.info(f"[lifecycle] Deduped {merged} duplicate ads")
    return {"merged": merged}


async def _merge_group(db: AsyncSession, *filters) -> int:
    """Merge a group of duplicate ads. Returns number of ads deactivated."""
    result = await db.execute(
        select(Ad)
        .where(*filters, Ad.is_active.is_(True))
        .order_by(Ad.last_seen.desc().nullslast())
    )
    ads = result.scalars().all()
    if len(ads) <= 1:
        return 0

    keeper = ads[0]
    merged = 0
    for dupe in ads[1:]:
        keeper.likes = max(keeper.likes or 0, dupe.likes or 0)
        keeper.comments = max(keeper.comments or 0, dupe.comments or 0)
        keeper.shares = max(keeper.shares or 0, dupe.shares or 0)
        keeper.collection_count = (keeper.collection_count or 1) + (dupe.collection_count or 1)
        if dupe.first_seen and (not keeper.first_seen or dupe.first_seen < keeper.first_seen):
            keeper.first_seen = dupe.first_seen
        if dupe.impressions_upper and (not keeper.impressions_upper or dupe.impressions_upper > keeper.impressions_upper):
            keeper.impressions_upper = dupe.impressions_upper
            keeper.impressions_lower = dupe.impressions_lower
        if dupe.spend_upper and (not keeper.spend_upper or dupe.spend_upper > keeper.spend_upper):
            keeper.spend_upper = dupe.spend_upper
            keeper.spend_lower = dupe.spend_lower
        dupe.is_active = False
        merged += 1

    return merged


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
