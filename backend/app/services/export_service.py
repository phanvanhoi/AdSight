import csv
import io

from elasticsearch import AsyncElasticsearch

from app.config import settings
from app.schemas.search import SearchRequest
from app.search.queries import build_search_query


async def export_ads_csv(es: AsyncElasticsearch, request: SearchRequest) -> str:
    query = build_search_query(request)

    response = await es.search(
        index=settings.es_ads_index,
        body=query,
        size=request.limit,
    )

    output = io.StringIO()
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
