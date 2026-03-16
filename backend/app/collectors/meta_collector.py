import logging
from datetime import datetime, timezone

import httpx

from app.collectors.base import BaseCollector
from app.config import settings

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

        headline = titles[0] if titles else None
        body_text = bodies[0] if bodies else None

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

        # Delivery dates
        start_time = raw_ad.get("ad_delivery_start_time")
        stop_time = raw_ad.get("ad_delivery_stop_time")

        return {
            "platform": "meta",
            "platform_ad_id": str(raw_ad.get("id", "")),
            "advertiser_id": raw_ad.get("page_id", ""),
            "advertiser_name": raw_ad.get("page_name", ""),
            "advertiser_page_url": f"https://facebook.com/{raw_ad.get('page_id', '')}",
            "ad_type": self._detect_ad_type(raw_ad),
            "headline": headline,
            "body_text": body_text,
            "cta_type": None,
            "media_urls": [],
            "media_s3_keys": [],
            "thumbnail_url": raw_ad.get("ad_snapshot_url"),
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
    "mỹ phẩm", "thời trang", "giảm giá", "khuyến mãi",
    "kem chống nắng", "serum", "điện thoại", "phụ kiện",
    "giày dép", "túi xách", "đồ ăn", "nhà hàng",
    "du lịch", "khóa học", "bất động sản", "xe máy",
]
