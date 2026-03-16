from datetime import datetime, timedelta, timezone

from elasticsearch import AsyncElasticsearch

from app.config import settings


async def get_dashboard_overview(es: AsyncElasticsearch) -> dict:
    index = settings.es_ads_index

    # Total ads
    total = await es.count(index=index)

    # Active ads
    active = await es.count(index=index, query={"term": {"is_active": True}})

    # Ads added last 24h
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    recent = await es.count(
        index=index,
        query={"range": {"last_seen": {"gte": yesterday.isoformat()}}},
    )

    # Top platforms
    platform_agg = await es.search(
        index=index,
        size=0,
        aggs={"platforms": {"terms": {"field": "platform", "size": 10}}},
    )
    platforms = {
        b["key"]: b["doc_count"]
        for b in platform_agg["aggregations"]["platforms"]["buckets"]
    }

    return {
        "total_ads": total["count"],
        "active_ads": active["count"],
        "ads_last_24h": recent["count"],
        "platforms": platforms,
    }


async def get_trending_ads(es: AsyncElasticsearch, limit: int = 20) -> list[dict]:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    response = await es.search(
        index=settings.es_ads_index,
        query={
            "bool": {
                "must": [
                    {"term": {"is_active": True}},
                    {"range": {"last_seen": {"gte": week_ago.isoformat()}}},
                ]
            }
        },
        sort=[
            {"likes": {"order": "desc", "missing": "_last"}},
            {"comments": {"order": "desc", "missing": "_last"}},
        ],
        size=limit,
    )

    return [
        {**hit["_source"], "id": hit["_id"]}
        for hit in response["hits"]["hits"]
    ]
