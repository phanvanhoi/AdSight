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
