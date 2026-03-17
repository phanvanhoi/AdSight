import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.collectors.base import BaseCollector, upsert_ads, index_ads_to_es
from app.config import settings
from app.core.database import async_session
from app.enrichment.pipeline import enrich_ads
from app.search.es_client import es_client

logger = logging.getLogger(__name__)

META_AD_LIBRARY_URL = f"https://graph.facebook.com/{settings.meta_api_version}/ads_archive"

# Fields to request from Meta Ad Library API
AD_FIELDS = [
    "id",
    "ad_creation_time",
    "ad_creative_bodies",
    "ad_creative_link_captions",
    "ad_creative_link_titles",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "bylines",
    "currency",
    "delivery_by_region",
    "demographic_distribution",
    "estimated_audience_size",
    "impressions",
    "languages",
    "page_id",
    "page_name",
    "publisher_platforms",
    "spend",
    "target_ages",
    "target_gender",
    "target_locations",
]


class RateLimitError(Exception):
    """Raised when Meta API returns 429."""
    pass


class MetaCollector(BaseCollector):
    def __init__(self):
        super().__init__(platform="meta")
        self.access_token = settings.meta_access_token

    async def collect(self, params: dict) -> list[dict]:
        """
        Collect ads from Meta Ad Library API.

        params:
            search_terms: str - keyword to search
            ad_reached_countries: list[str] - e.g. ["VN"]
            ad_type: str - "ALL" | "POLITICAL_AND_ISSUE_ADS"
            limit: int - results per page (max 1000)
            max_pages: int - max pagination pages
        """
        search_terms = params.get("search_terms", "")
        countries = params.get("ad_reached_countries", ["VN"])
        ad_type = params.get("ad_type", "ALL")
        limit = params.get("limit", 100)
        max_pages = params.get("max_pages", 5)

        all_ads = []

        async with httpx.AsyncClient(timeout=30) as client:
            request_params = {
                "access_token": self.access_token,
                "search_terms": search_terms,
                "ad_reached_countries": countries,
                "ad_type": ad_type,
                "fields": ",".join(AD_FIELDS),
                "limit": min(limit, 1000),
            }

            url = META_AD_LIBRARY_URL
            page = 0

            while url and page < max_pages:
                try:
                    response = await client.get(url, params=request_params if page == 0 else None)

                    if response.status_code == 429:
                        raise RateLimitError(f"Rate limited by Meta API (429)")

                    response.raise_for_status()
                    data = response.json()

                    ads = data.get("data", [])
                    all_ads.extend(ads)

                    logger.info(f"[meta] Page {page + 1}: fetched {len(ads)} ads")

                    # Pagination
                    paging = data.get("paging", {})
                    url = paging.get("next")
                    request_params = None  # next URL includes params
                    page += 1

                except RateLimitError:
                    raise  # Let retry handler deal with it
                except httpx.HTTPStatusError as e:
                    logger.error(f"[meta] HTTP error: {e.response.status_code} - {e.response.text}")
                    break
                except Exception as e:
                    logger.error(f"[meta] Error fetching ads: {e}")
                    break

        return all_ads

    @staticmethod
    def _detect_ad_type(raw_ad: dict) -> str:
        """Infer ad type from available creative data."""
        snapshot_url = raw_ad.get("ad_snapshot_url", "")
        bodies = raw_ad.get("ad_creative_bodies", [])
        link_titles = raw_ad.get("ad_creative_link_titles", [])
        if len(bodies) > 1 or len(link_titles) > 1:
            return "carousel"
        if "video" in snapshot_url.lower():
            return "video"
        return "image"

    def normalize(self, raw_ad: dict) -> dict:
        """Convert Meta Ad Library format to internal schema."""
        now = datetime.now(timezone.utc).isoformat()

        # Extract text content
        bodies = raw_ad.get("ad_creative_bodies", [])
        titles = raw_ad.get("ad_creative_link_titles", [])
        captions = raw_ad.get("ad_creative_link_captions", [])

        headline = " | ".join(titles) if titles else None
        body_text = " | ".join(bodies) if bodies else None
        cta_type = captions[0] if captions else None

        # Extract spend
        spend = raw_ad.get("spend", {})
        spend_lower = float(spend.get("lower_bound", 0)) if spend else None
        spend_upper = float(spend.get("upper_bound", 0)) if spend else None

        # Extract impressions
        impressions = raw_ad.get("impressions", {})
        imp_lower = int(impressions.get("lower_bound", 0)) if impressions else None
        imp_upper = int(impressions.get("upper_bound", 0)) if impressions else None

        # Extract targeting
        target_ages = raw_ad.get("target_ages", "")
        target_gender = raw_ad.get("target_gender", "")
        target_locations = raw_ad.get("target_locations", {})
        countries = []
        if isinstance(target_locations, dict):
            countries = target_locations.get("countries", [])
        elif isinstance(target_locations, list):
            countries = target_locations

        # Bylines → advertiser page URL
        bylines = raw_ad.get("bylines", "")
        advertiser_page_url = None
        page_id = raw_ad.get("page_id", "")
        if page_id:
            advertiser_page_url = f"https://facebook.com/{page_id}"

        # Delivery dates
        start_time = raw_ad.get("ad_delivery_start_time")
        stop_time = raw_ad.get("ad_delivery_stop_time")

        # Snapshot URL as media
        snapshot_url = raw_ad.get("ad_snapshot_url")
        media_urls = [snapshot_url] if snapshot_url else []

        # Demographics
        demographic_distribution = raw_ad.get("demographic_distribution")
        publisher_platforms = raw_ad.get("publisher_platforms", [])

        return {
            "platform": "meta",
            "platform_ad_id": str(raw_ad.get("id", "")),
            "advertiser_id": page_id,
            "advertiser_name": raw_ad.get("page_name", ""),
            "advertiser_page_url": advertiser_page_url,
            "ad_type": self._detect_ad_type(raw_ad),
            "headline": headline,
            "body_text": body_text,
            "cta_type": cta_type,
            "media_urls": media_urls,
            "media_s3_keys": [],
            "thumbnail_url": snapshot_url,
            "landing_page_url": None,
            "target_countries": countries if countries else ["VN"],
            "target_age_min": None,
            "target_age_max": None,
            "target_gender": target_gender if target_gender else None,
            "target_interests": [],
            "impressions_lower": imp_lower,
            "impressions_upper": imp_upper,
            "spend_lower": spend_lower,
            "spend_upper": spend_upper,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "language": raw_ad.get("languages", ["vi"])[0] if raw_ad.get("languages") else "vi",
            "category": None,
            "tags": [],
            "sentiment": None,
            "first_seen": start_time or now,
            "last_seen": stop_time or now,
            "is_active": stop_time is None,
            "created_at": now,
        }


# Default search terms for VN market
VN_SEARCH_TERMS = [
    # AI & Chatbot
    "AI tool", "chatbot", "artificial intelligence", "GPT", "AI assistant",
    # SaaS & Software
    "SaaS", "software", "phần mềm", "ứng dụng", "app",
    # Business tools
    "CRM", "ERP", "marketing tool", "automation", "workflow",
    # Productivity & Cloud
    "productivity", "project management", "cloud", "no code", "low code",
    # Specific niches
    "email marketing", "landing page", "analytics", "SEO tool", "ads manager",
]


async def collect_and_store(search_terms: str | None = None) -> dict:
    """
    Fetch ads from Meta Ad Library, normalize, upsert to DB, index to ES.
    Returns stats: {"fetched": N, "new": M, "updated": K}
    """
    collector = MetaCollector()
    terms = [search_terms] if search_terms else VN_SEARCH_TERMS

    await es_client.initialize()
    es = es_client.client

    total_fetched = 0
    total_new = 0
    total_updated = 0

    try:
        for term in terms:
            try:
                ads = await collector.collect_with_retry({
                    "search_terms": term,
                    "ad_reached_countries": ["VN"],
                    "limit": 100,
                    "max_pages": 3,
                })
                total_fetched += len(ads)

                if ads:
                    async with async_session() as db:
                        result = await upsert_ads(db, ads)
                        total_new += result["new"]
                        total_updated += result["updated"]
                        await index_ads_to_es(es, result["ads"])
                        # Enrich newly upserted ads
                        ad_ids = [a["id"] for a in result["ads"] if a.get("id")]
                        if ad_ids:
                            await enrich_ads(db, ad_ids=ad_ids)

                    logger.info(f"[meta] '{term}': {result['new']} new, {result['updated']} updated")
            except Exception as e:
                logger.error(f"[meta] Error collecting '{term}': {e}", exc_info=True)
    finally:
        await es_client.close()

    stats = {"fetched": total_fetched, "new": total_new, "updated": total_updated}
    logger.info(f"[meta] Collection complete: {stats}")
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(collect_and_store())
    print(f"Meta collection done: {result}")
