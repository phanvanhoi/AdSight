import logging
from datetime import datetime, timezone

import httpx

from app.collectors.base import BaseCollector, upsert_ads, index_ads_to_es
from app.config import settings
from app.core.database import async_session
from app.enrichment.pipeline import enrich_ads
from app.search.es_client import es_client

logger = logging.getLogger(__name__)


class TikTokCollector(BaseCollector):
    def __init__(self):
        super().__init__(platform="tiktok")
        self.base_url = settings.tiktok_api_base_url

    async def collect(self, params: dict) -> list[dict]:
        """
        Collect ads from TikTok Creative Center API.

        params:
            country_code: str - e.g. "VN"
            industry_id: str - industry filter
            period: int - 7, 30, 180 days
            limit: int
            max_pages: int
        """
        country_code = params.get("country_code", "VN")
        period = params.get("period", 30)
        limit = params.get("limit", 50)
        max_pages = params.get("max_pages", 5)

        all_ads = []

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(1, max_pages + 1):
                try:
                    response = await client.get(
                        f"{self.base_url}/top_ads/list",
                        params={
                            "country_code": country_code,
                            "period": period,
                            "page": page,
                            "limit": limit,
                            "order_by": "like",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    ads = data.get("data", {}).get("materials", [])
                    if not ads:
                        break

                    all_ads.extend(ads)
                    logger.info(f"[tiktok] Page {page}: fetched {len(ads)} ads")

                except httpx.HTTPStatusError as e:
                    logger.error(f"[tiktok] HTTP error: {e.response.status_code}")
                    break
                except Exception as e:
                    logger.error(f"[tiktok] Error: {e}")
                    break

        return all_ads

    def normalize(self, raw_ad: dict) -> dict:
        """Convert TikTok Creative Center format to internal schema."""
        now = datetime.now(timezone.utc).isoformat()

        # Extract video info
        video_info = raw_ad.get("video_info", {})
        cover_url = video_info.get("cover", "")
        video_url = video_info.get("url", "")

        return {
            "platform": "tiktok",
            "platform_ad_id": str(raw_ad.get("id", raw_ad.get("material_id", ""))),
            "advertiser_id": raw_ad.get("advertiser_id", ""),
            "advertiser_name": raw_ad.get("brand_name", raw_ad.get("advertiser_name", "")),
            "advertiser_page_url": None,
            "ad_type": "video",
            "headline": raw_ad.get("ad_title", raw_ad.get("title", "")),
            "body_text": raw_ad.get("ad_text", raw_ad.get("text", raw_ad.get("caption", ""))),
            "cta_type": raw_ad.get("cta", None),
            "media_urls": [video_url] if video_url else [],
            "media_s3_keys": [],
            "thumbnail_url": cover_url or None,
            "landing_page_url": raw_ad.get("landing_page_url", raw_ad.get("landing_page", None)),
            "target_countries": [raw_ad.get("country_code", "VN")],
            "target_age_min": None,
            "target_age_max": None,
            "target_gender": None,
            "target_interests": [],
            "impressions_lower": None,
            "impressions_upper": None,
            "spend_lower": None,
            "spend_upper": None,
            "likes": raw_ad.get("like", 0) or 0,
            "comments": raw_ad.get("comment", 0) or 0,
            "shares": raw_ad.get("share", 0) or 0,
            "language": "vi",
            "category": raw_ad.get("industry_name", None),
            "tags": raw_ad.get("tag", []) if isinstance(raw_ad.get("tag"), list) else [],
            "sentiment": None,
            "first_seen": raw_ad.get("create_time", now),
            "last_seen": now,
            "is_active": True,
            "created_at": now,
        }


async def collect_and_store(country_code: str = "VN", period: int = 30) -> dict:
    """
    Fetch ads from TikTok Creative Center, normalize, upsert to DB, index to ES.
    Returns stats: {"fetched": N, "new": M, "updated": K}
    """
    collector = TikTokCollector()

    es = None
    try:
        await es_client.initialize()
        es = es_client.client
    except Exception:
        logger.warning("[tiktok] ES unavailable, skipping indexing")

    total_fetched = 0
    total_new = 0
    total_updated = 0

    try:
        ads = await collector.collect_with_retry({
            "country_code": country_code,
            "period": period,
            "limit": 50,
            "max_pages": 5,
        })
        total_fetched = len(ads)

        if ads:
            async with async_session() as db:
                result = await upsert_ads(db, ads)
                total_new = result["new"]
                total_updated = result["updated"]
                if es:
                    await index_ads_to_es(es, result["ads"])
                # Enrich newly upserted ads
                ad_ids = [a["id"] for a in result["ads"] if a.get("id")]
                if ad_ids:
                    await enrich_ads(db, ad_ids=ad_ids)
    except Exception as e:
        logger.error(f"[tiktok] Error: {e}", exc_info=True)
    finally:
        if es:
            await es_client.close()

    stats = {"fetched": total_fetched, "new": total_new, "updated": total_updated}
    logger.info(f"[tiktok] Collection complete: {stats}")
    return stats


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(collect_and_store(country_code="VN", period=30))
    print(f"TikTok collection done: {result}")
