"""
Google Ads Transparency Center collector.
Collects ads visible in Google's transparency center for VN market.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.collectors.base import BaseCollector, upsert_ads, index_ads_to_es
from app.config import settings
from app.core.database import async_session
from app.enrichment.pipeline import enrich_ads
from app.search.es_client import es_client

logger = logging.getLogger(__name__)

# Google Ads Transparency undocumented API (reverse-engineered)
TRANSPARENCY_API = "https://adstransparency.google.com/anji/_/rpc/SearchService/SearchCreatives"


class GoogleAdsCollector(BaseCollector):
    def __init__(self):
        super().__init__(platform="google")

    async def collect(self, params: dict) -> list[dict]:
        """
        Collect ads from Google Ads Transparency Center.

        params:
            query: str - search keyword
            country: str - "VN"
            max_pages: int
            limit: int - results per page
        """
        query = params.get("query", "")
        country = params.get("country", "VN")
        max_pages = params.get("max_pages", 3)
        limit = params.get("limit", 30)

        all_ads = []

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(max_pages):
                try:
                    request_data = {
                        "query": query,
                        "region": country,
                        "date_range": "LAST_30_DAYS",
                        "platform": "ALL",
                        "offset": page * limit,
                        "limit": limit,
                    }

                    response = await client.post(
                        TRANSPARENCY_API,
                        json=request_data,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        },
                    )

                    if response.status_code != 200:
                        logger.warning(f"[google] HTTP {response.status_code} on page {page + 1}")
                        break

                    data = response.json()
                    ads = data.get("creatives", data.get("results", []))

                    if not ads:
                        break

                    all_ads.extend(ads)
                    logger.info(f"[google] Page {page + 1}: fetched {len(ads)} ads")

                except Exception as e:
                    logger.error(f"[google] Error on page {page + 1}: {e}")
                    break

        return all_ads

    def normalize(self, raw_ad: dict) -> dict:
        """Convert Google Ads Transparency format to internal schema."""
        now = datetime.now(timezone.utc).isoformat()

        ad_id = raw_ad.get("creative_id", raw_ad.get("id", ""))

        # Detect ad type
        ad_format = raw_ad.get("format", raw_ad.get("creative_type", "")).upper()
        if "VIDEO" in ad_format or "YOUTUBE" in ad_format:
            ad_type = "video"
        elif "IMAGE" in ad_format or "DISPLAY" in ad_format:
            ad_type = "image"
        else:
            ad_type = "text"

        headline = raw_ad.get("headline", raw_ad.get("title", ""))
        description = raw_ad.get("description", raw_ad.get("body", ""))
        platforms = raw_ad.get("platforms", [])

        return {
            "platform": "google",
            "platform_ad_id": str(ad_id),
            "advertiser_id": raw_ad.get("advertiser_id", ""),
            "advertiser_name": raw_ad.get("advertiser_name", raw_ad.get("advertiser", "")),
            "advertiser_page_url": None,
            "ad_type": ad_type,
            "headline": headline if headline else None,
            "body_text": description if description else None,
            "cta_type": None,
            "media_urls": [raw_ad.get("image_url")] if raw_ad.get("image_url") else [],
            "media_s3_keys": [],
            "thumbnail_url": raw_ad.get("image_url") or raw_ad.get("video_thumbnail"),
            "landing_page_url": raw_ad.get("destination_url", raw_ad.get("landing_page")),
            "target_countries": [raw_ad.get("region", "VN")],
            "target_age_min": None,
            "target_age_max": None,
            "target_gender": None,
            "target_interests": [],
            "impressions_lower": None,
            "impressions_upper": None,
            "spend_lower": None,
            "spend_upper": None,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "language": "vi",
            "category": None,
            "tags": platforms,
            "sentiment": None,
            "first_seen": raw_ad.get("first_shown", now),
            "last_seen": raw_ad.get("last_shown", now),
            "is_active": True,
            "created_at": now,
        }


VN_SEARCH_TERMS_GOOGLE = [
    "mua hàng online", "khuyến mãi", "giảm giá",
    "đăng ký", "tải app", "dịch vụ",
    "bất động sản", "vay tiền", "bảo hiểm",
    "du lịch việt nam", "khóa học",
]


async def collect_and_store(search_terms: str | None = None) -> dict:
    """Fetch, normalize, upsert, index, enrich."""
    collector = GoogleAdsCollector()
    terms = [search_terms] if search_terms else VN_SEARCH_TERMS_GOOGLE

    await es_client.initialize()
    es = es_client.client

    total_fetched = 0
    total_new = 0
    total_updated = 0

    try:
        for term in terms:
            try:
                ads = await collector.collect_with_retry({
                    "query": term,
                    "country": "VN",
                    "limit": 30,
                    "max_pages": 3,
                })
                total_fetched += len(ads)

                if ads:
                    async with async_session() as db:
                        result = await upsert_ads(db, ads)
                        total_new += result["new"]
                        total_updated += result["updated"]
                        await index_ads_to_es(es, result["ads"])

                        ad_ids = [a["id"] for a in result["ads"] if a.get("id")]
                        if ad_ids:
                            await enrich_ads(db, ad_ids=ad_ids)

            except Exception as e:
                logger.error(f"[google] Error collecting '{term}': {e}", exc_info=True)
    finally:
        await es_client.close()

    stats = {"fetched": total_fetched, "new": total_new, "updated": total_updated}
    logger.info(f"[google] Collection complete: {stats}")
    return stats
