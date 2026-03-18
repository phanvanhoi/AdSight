"""Postgres fallback for search when Elasticsearch is unavailable."""
from datetime import datetime, date

from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.schemas.search import AdSummary, Facets, SearchRequest, SearchResponse


async def search_ads_pg(db: AsyncSession, request: SearchRequest) -> SearchResponse:
    query = select(Ad)

    # Text search
    if request.q:
        pattern = f"%{request.q}%"
        query = query.where(
            or_(
                Ad.headline.ilike(pattern),
                Ad.body_text.ilike(pattern),
                Ad.advertiser_name.ilike(pattern),
            )
        )

    # Filters
    if request.platform:
        query = query.where(Ad.platform == request.platform)
    if request.ad_type:
        query = query.where(Ad.ad_type == request.ad_type)
    if request.country:
        query = query.where(Ad.country == request.country)
    if request.date_from:
        query = query.where(Ad.first_seen >= request.date_from)
    if request.date_to:
        query = query.where(Ad.last_seen <= request.date_to)
    if request.min_likes:
        query = query.where(Ad.likes >= request.min_likes)
    if request.category_l1:
        query = query.where(Ad.category_l1 == request.category_l1)
    if request.category_l2:
        query = query.where(Ad.category_l2 == request.category_l2)
    if request.min_viral_score is not None:
        query = query.where(Ad.viral_score >= request.min_viral_score)
    if request.is_hot is not None:
        query = query.where(Ad.is_hot == request.is_hot)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sort
    sort_map = {
        "newest": desc(Ad.last_seen),
        "oldest": asc(Ad.first_seen),
        "most_likes": desc(Ad.likes),
        "viral": desc(Ad.viral_score),
    }
    order = sort_map.get(request.sort, desc(Ad.last_seen))
    query = query.order_by(order)

    # Pagination
    offset = (request.page - 1) * request.limit
    query = query.offset(offset).limit(request.limit)

    result = await db.execute(query)
    ads = result.scalars().all()

    results = []
    for ad in ads:
        days = 0
        if ad.first_seen and ad.last_seen:
            try:
                first = ad.first_seen if isinstance(ad.first_seen, (datetime, date)) else datetime.fromisoformat(str(ad.first_seen))
                last = ad.last_seen if isinstance(ad.last_seen, (datetime, date)) else datetime.fromisoformat(str(ad.last_seen))
                days = max((last - first).days, 1)
            except (ValueError, TypeError):
                days = 0

        results.append(AdSummary(
            id=str(ad.id),
            platform=ad.platform or "",
            advertiser_name=ad.advertiser_name,
            ad_type=ad.ad_type or "image",
            headline=ad.headline,
            body_text=(ad.body_text or "")[:200] or None,
            thumbnail_url=ad.thumbnail_url,
            cta_type=ad.cta_type,
            likes=ad.likes or 0,
            comments=ad.comments or 0,
            shares=ad.shares or 0,
            first_seen=str(ad.first_seen) if ad.first_seen else None,
            last_seen=str(ad.last_seen) if ad.last_seen else None,
            is_active=ad.is_active if ad.is_active is not None else True,
            days_running=days,
            category_l1=ad.category_l1,
            category_l2=ad.category_l2,
            viral_score=ad.viral_score,
            is_hot=ad.is_hot or False,
        ))

    # Facets from DB
    facets = Facets()
    platform_q = select(Ad.platform, func.count()).group_by(Ad.platform)
    for row in (await db.execute(platform_q)).all():
        if row[0]:
            facets.platforms[row[0]] = row[1]

    type_q = select(Ad.ad_type, func.count()).group_by(Ad.ad_type)
    for row in (await db.execute(type_q)).all():
        if row[0]:
            facets.ad_types[row[0]] = row[1]

    return SearchResponse(
        total=total,
        page=request.page,
        limit=request.limit,
        results=results,
        facets=facets,
    )
