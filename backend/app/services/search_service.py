from datetime import datetime

from elasticsearch import AsyncElasticsearch

from app.config import settings
from app.schemas.search import AdSummary, Facets, SearchRequest, SearchResponse
from app.search.queries import build_search_query


async def search_ads(es: AsyncElasticsearch, request: SearchRequest) -> SearchResponse:
    query = build_search_query(request)
    offset = (request.page - 1) * request.limit

    response = await es.search(
        index=settings.es_ads_index,
        query=query.get("query"),
        sort=query.get("sort"),
        aggs=query.get("aggs"),
        from_=offset,
        size=request.limit,
    )

    hits = response["hits"]
    total = hits["total"]["value"]

    results = []
    for hit in hits["hits"]:
        src = hit["_source"]
        # Calculate days running
        days = 0
        if src.get("first_seen") and src.get("last_seen"):
            try:
                first = datetime.fromisoformat(src["first_seen"])
                last = datetime.fromisoformat(src["last_seen"])
                days = max((last - first).days, 1)
            except (ValueError, TypeError):
                days = 0

        results.append(AdSummary(
            id=hit["_id"],
            platform=src.get("platform", ""),
            advertiser_name=src.get("advertiser_name"),
            ad_type=src.get("ad_type", "image"),
            headline=src.get("headline"),
            body_text=src.get("body_text", "")[:200] if src.get("body_text") else None,
            thumbnail_url=src.get("thumbnail_url"),
            cta_type=src.get("cta_type"),
            likes=src.get("likes", 0) or 0,
            comments=src.get("comments", 0) or 0,
            shares=src.get("shares", 0) or 0,
            first_seen=src.get("first_seen"),
            last_seen=src.get("last_seen"),
            is_active=src.get("is_active", True),
            days_running=days,
        ))

    # Parse facets from aggregations
    facets = Facets()
    aggs = response.get("aggregations", {})
    if "platforms" in aggs:
        facets.platforms = {
            b["key"]: b["doc_count"] for b in aggs["platforms"]["buckets"]
        }
    if "ad_types" in aggs:
        facets.ad_types = {
            b["key"]: b["doc_count"] for b in aggs["ad_types"]["buckets"]
        }
    if "categories" in aggs:
        facets.categories = {
            b["key"]: b["doc_count"] for b in aggs["categories"]["buckets"]
        }

    return SearchResponse(
        total=total,
        page=request.page,
        limit=request.limit,
        results=results,
        facets=facets,
    )
