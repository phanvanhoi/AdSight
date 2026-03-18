import csv
import io

from elasticsearch import AsyncElasticsearch
from sqlalchemy import select, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.ad import Ad
from app.schemas.search import ExportSearchRequest
from app.search.queries import build_search_query


async def export_ads_csv_pg(db: AsyncSession, request: ExportSearchRequest) -> str:
    """Postgres fallback for CSV export."""
    query = select(Ad)
    if request.q:
        pattern = f"%{request.q}%"
        query = query.where(or_(Ad.headline.ilike(pattern), Ad.body_text.ilike(pattern)))
    if request.platform:
        query = query.where(Ad.platform == request.platform)
    if request.country:
        query = query.where(Ad.country == request.country)
    if request.ad_type:
        query = query.where(Ad.ad_type == request.ad_type)

    sort_map = {"newest": desc(Ad.last_seen), "oldest": asc(Ad.first_seen), "most_likes": desc(Ad.likes)}
    query = query.order_by(sort_map.get(request.sort, desc(Ad.last_seen))).limit(request.limit)

    result = await db.execute(query)
    ads = result.scalars().all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "Platform", "Advertiser", "Headline", "Body Text", "Ad Type",
        "CTA", "Landing Page", "Likes", "Comments", "Shares",
        "First Seen", "Last Seen", "Active", "Country",
    ])
    for ad in ads:
        countries = ad.target_countries or []
        writer.writerow([
            ad.platform or "", ad.advertiser_name or "", ad.headline or "",
            (ad.body_text or "")[:500], ad.ad_type or "", ad.cta_type or "",
            ad.landing_page_url or "", ad.likes or 0, ad.comments or 0, ad.shares or 0,
            str(ad.first_seen) if ad.first_seen else "", str(ad.last_seen) if ad.last_seen else "",
            ad.is_active, ",".join(countries) if isinstance(countries, list) else str(countries),
        ])
    return output.getvalue()


async def export_ads_csv(es: AsyncElasticsearch, request: ExportSearchRequest) -> str:
    query = build_search_query(request)

    response = await es.search(
        index=settings.es_ads_index,
        query=query.get("query"),
        sort=query.get("sort"),
        size=request.limit,
    )

    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM for Vietnamese characters in Excel
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Platform", "Advertiser", "Headline", "Body Text", "Ad Type",
        "CTA", "Landing Page", "Likes", "Comments", "Shares",
        "First Seen", "Last Seen", "Active", "Country",
    ])

    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        countries = src.get("target_countries", [])
        writer.writerow([
            src.get("platform", ""),
            src.get("advertiser_name", ""),
            src.get("headline", ""),
            (src.get("body_text", "") or "")[:500],
            src.get("ad_type", ""),
            src.get("cta_type", ""),
            src.get("landing_page_url", ""),
            src.get("likes", 0),
            src.get("comments", 0),
            src.get("shares", 0),
            src.get("first_seen", ""),
            src.get("last_seen", ""),
            src.get("is_active", True),
            ",".join(countries) if isinstance(countries, list) else str(countries),
        ])

    return output.getvalue()
