from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.ad import Ad
from app.models.advertiser_group import AdvertiserGroup

router = APIRouter()


@router.get("/")
async def list_advertiser_groups(
    q: str | None = None,
    platform: str | None = None,
    sort: str = "total_ads",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List cross-platform advertiser groups."""
    stmt = select(AdvertiserGroup)

    if q:
        stmt = stmt.where(AdvertiserGroup.name.ilike(f"%{q}%"))

    if sort == "total_spend":
        stmt = stmt.order_by(desc(AdvertiserGroup.total_estimated_spend))
    elif sort == "name":
        stmt = stmt.order_by(AdvertiserGroup.name)
    else:
        stmt = stmt.order_by(desc(AdvertiserGroup.total_ads))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    groups = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [
            {
                "id": str(g.id),
                "name": g.name,
                "slug": g.slug,
                "platform_ids": g.platform_ids,
                "total_ads": g.total_ads,
                "total_estimated_spend": g.total_estimated_spend,
                "is_verified": g.is_verified,
            }
            for g in groups
        ],
    }


@router.get("/{group_id}")
async def get_advertiser_group(group_id: str, db: AsyncSession = Depends(get_db)):
    """Get advertiser group with summary."""
    result = await db.execute(
        select(AdvertiserGroup).where(AdvertiserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return {
        "id": str(group.id),
        "name": group.name,
        "slug": group.slug,
        "platform_ids": group.platform_ids,
        "total_ads": group.total_ads,
        "total_estimated_spend": group.total_estimated_spend,
        "categories": group.categories,
        "is_verified": group.is_verified,
    }


@router.get("/{group_id}/analytics")
async def get_advertiser_analytics(group_id: str, db: AsyncSession = Depends(get_db)):
    """Get analytics for an advertiser group."""
    result = await db.execute(
        select(AdvertiserGroup).where(AdvertiserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Build conditions from platform_ids
    conditions = []
    if group.platform_ids:
        for plat, ids in group.platform_ids.items():
            if ids:
                conditions.append((Ad.platform == plat) & (Ad.advertiser_id.in_(ids)))

    if not conditions:
        return {
            "platform_breakdown": {},
            "ads_timeline": [],
            "category_breakdown": {},
            "top_ads": [],
            "ad_type_breakdown": {},
            "avg_engagement_rate": 0,
            "avg_viral_score": 0,
            "total_active_ads": 0,
            "first_ad_date": None,
            "latest_ad_date": None,
        }

    ads_result = await db.execute(select(Ad).where(or_(*conditions)))
    ads = ads_result.scalars().all()

    # Platform breakdown
    platform_breakdown: dict = {}
    for ad in ads:
        if ad.platform not in platform_breakdown:
            platform_breakdown[ad.platform] = {"count": 0, "total_spend": 0}
        platform_breakdown[ad.platform]["count"] += 1
        platform_breakdown[ad.platform]["total_spend"] += ad.estimated_total_spend or 0

    # Ads timeline (group by month)
    month_counts: Counter = Counter()
    for ad in ads:
        if ad.first_seen:
            month_key = ad.first_seen.strftime("%Y-%m")
            month_counts[month_key] += 1
    ads_timeline = [{"month": m, "count": c} for m, c in sorted(month_counts.items())]

    # Category breakdown
    cat_counts = Counter(ad.category_l1 for ad in ads if ad.category_l1)

    # Ad type breakdown
    type_counts = Counter(ad.ad_type for ad in ads)

    # Top ads by viral_score
    top_ads = sorted(
        [a for a in ads if a.viral_score],
        key=lambda a: a.viral_score,
        reverse=True,
    )[:5]

    # Stats
    engagement_rates = [a.engagement_rate for a in ads if a.engagement_rate]
    viral_scores = [a.viral_score for a in ads if a.viral_score]
    active_count = sum(1 for a in ads if a.is_active)
    dates = [a.first_seen for a in ads if a.first_seen]

    return {
        "platform_breakdown": platform_breakdown,
        "ads_timeline": ads_timeline,
        "category_breakdown": dict(cat_counts),
        "top_ads": [
            {
                "id": str(a.id),
                "headline": a.headline,
                "likes": a.likes,
                "viral_score": a.viral_score,
                "platform": a.platform,
            }
            for a in top_ads
        ],
        "ad_type_breakdown": dict(type_counts),
        "avg_engagement_rate": round(sum(engagement_rates) / len(engagement_rates), 1) if engagement_rates else 0,
        "avg_viral_score": round(sum(viral_scores) / len(viral_scores), 1) if viral_scores else 0,
        "total_active_ads": active_count,
        "first_ad_date": str(min(dates).date()) if dates else None,
        "latest_ad_date": str(max(dates).date()) if dates else None,
    }


@router.get("/{group_id}/ads")
async def get_advertiser_ads(
    group_id: str,
    platform: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all ads for an advertiser group."""
    group_result = await db.execute(
        select(AdvertiserGroup).where(AdvertiserGroup.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Build filter: match by advertiser_id across platforms
    conditions = []
    if group.platform_ids:
        for plat, ids in group.platform_ids.items():
            if ids:
                conditions.append(
                    (Ad.platform == plat) & (Ad.advertiser_id.in_(ids))
                )

    if not conditions:
        return {"total": 0, "page": page, "limit": limit, "results": []}

    base_filter = select(Ad).where(or_(*conditions))

    if platform:
        base_filter = base_filter.where(Ad.platform == platform)

    # Total count (before pagination)
    count_stmt = select(func.count()).select_from(base_filter.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base_filter.order_by(desc(Ad.first_seen))

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    ads = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [
            {
                "id": str(a.id),
                "platform": a.platform,
                "advertiser_name": a.advertiser_name,
                "headline": a.headline,
                "ad_type": a.ad_type,
                "first_seen": str(a.first_seen) if a.first_seen else None,
                "likes": a.likes,
                "viral_score": a.viral_score,
            }
            for a in ads
        ],
    }
