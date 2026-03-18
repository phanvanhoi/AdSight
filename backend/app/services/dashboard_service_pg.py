"""Postgres fallback for dashboard when Elasticsearch is unavailable."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad


async def get_dashboard_overview_pg(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count(Ad.id)))).scalar() or 0
    active = (await db.execute(
        select(func.count(Ad.id)).where(Ad.is_active == True)  # noqa: E712
    )).scalar() or 0

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent = (await db.execute(
        select(func.count(Ad.id)).where(Ad.last_seen >= yesterday)
    )).scalar() or 0

    platform_rows = (await db.execute(
        select(Ad.platform, func.count()).group_by(Ad.platform)
    )).all()
    platforms = {row[0]: row[1] for row in platform_rows if row[0]}

    return {
        "total_ads": total,
        "active_ads": active,
        "ads_last_24h": recent,
        "platforms": platforms,
    }


async def get_trending_ads_pg(db: AsyncSession, limit: int = 20) -> list[dict]:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    query = (
        select(Ad)
        .where(Ad.is_active == True, Ad.last_seen >= week_ago)  # noqa: E712
        .order_by(desc(Ad.viral_score), desc(Ad.likes), desc(Ad.comments))
        .limit(limit)
    )

    result = await db.execute(query)
    ads = result.scalars().all()

    trending = []
    for ad in ads:
        trending.append({
            "id": str(ad.id),
            "platform": ad.platform,
            "advertiser_name": ad.advertiser_name,
            "headline": ad.headline,
            "body_text": (ad.body_text or "")[:200] or None,
            "thumbnail_url": ad.thumbnail_url,
            "ad_type": ad.ad_type,
            "cta_type": ad.cta_type,
            "likes": ad.likes or 0,
            "comments": ad.comments or 0,
            "shares": ad.shares or 0,
            "viral_score": ad.viral_score,
            "is_hot": ad.is_hot or False,
            "is_active": ad.is_active,
            "first_seen": str(ad.first_seen) if ad.first_seen else None,
            "last_seen": str(ad.last_seen) if ad.last_seen else None,
            "collection_count": ad.collection_count or 1,
        })

    return trending
