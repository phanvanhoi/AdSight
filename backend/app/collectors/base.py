import abc
import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone

from dateutil.parser import parse as parse_date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.search.indexing import bulk_index_ads

logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    """Abstract base for all platform data collectors."""

    def __init__(self, platform: str):
        self.platform = platform

    @abc.abstractmethod
    async def collect(self, params: dict) -> list[dict]:
        """Fetch raw ads from the platform. Returns list of raw ad dicts."""
        ...

    @abc.abstractmethod
    def normalize(self, raw_ad: dict) -> dict:
        """Convert platform-specific format to our internal Ad schema."""
        ...

    async def collect_and_normalize(self, params: dict) -> list[dict]:
        """Collect raw ads and normalize them."""
        raw_ads = await self.collect(params)
        logger.info(f"[{self.platform}] Collected {len(raw_ads)} raw ads")

        normalized = []
        for raw in raw_ads:
            try:
                ad = self.normalize(raw)
                normalized.append(ad)
            except Exception as e:
                logger.warning(f"[{self.platform}] Failed to normalize ad: {e}")
                continue

        logger.info(f"[{self.platform}] Normalized {len(normalized)} ads")
        return normalized

    async def collect_with_retry(self, params: dict, max_retries: int = 3) -> list[dict]:
        """Collect with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return await self.collect_and_normalize(params)
            except Exception as e:
                wait = 2 ** attempt
                logger.error(
                    f"[{self.platform}] Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait}s..."
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"[{self.platform}] All retries exhausted")
                    raise
        return []


def _to_datetime(value) -> datetime | None:
    """Convert a string or datetime to a datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return parse_date(value)
    except (ValueError, TypeError):
        return None


def _compute_content_hash(ad_data: dict) -> str | None:
    """Compute SHA-256 hash of ad text content for deduplication."""
    parts = []
    for field in ("headline", "body_text"):
        val = ad_data.get(field)
        if val:
            # Normalize whitespace for consistent hashing
            parts.append(" ".join(val.split()))
    if not parts:
        return None
    raw = "|".join(parts).lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


async def upsert_ads(db: AsyncSession, ads: list[dict]) -> dict:
    """
    Bulk upsert ads into PostgreSQL.
    - If platform_ad_id already exists -> update metrics (only if new value > 0)
    - If not -> insert new record
    Returns {"new": N, "updated": M}
    """
    new_count = 0
    updated_count = 0
    ads_with_ids = []

    for ad_data in ads:
        platform = ad_data["platform"]
        platform_ad_id = ad_data["platform_ad_id"]

        # Compute content hash for text-based deduplication
        content_hash = _compute_content_hash(ad_data)

        result = await db.execute(
            select(Ad).where(
                Ad.platform == platform,
                Ad.platform_ad_id == platform_ad_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.last_seen = datetime.now(timezone.utc)
            existing.collection_count = (existing.collection_count or 1) + 1
            existing.is_active = ad_data.get("is_active", existing.is_active)
            if content_hash:
                existing.content_hash = content_hash

            # Only update engagement if new value > existing (don't overwrite with 0)
            for field in ("likes", "comments", "shares"):
                new_val = ad_data.get(field, 0) or 0
                old_val = getattr(existing, field) or 0
                if new_val > old_val:
                    setattr(existing, field, new_val)

            # Only update impressions/spend if new value is provided (not None)
            if ad_data.get("impressions_lower") is not None:
                existing.impressions_lower = ad_data["impressions_lower"]
            if ad_data.get("impressions_upper") is not None:
                existing.impressions_upper = ad_data["impressions_upper"]
            if ad_data.get("spend_lower") is not None:
                existing.spend_lower = ad_data["spend_lower"]
            if ad_data.get("spend_upper") is not None:
                existing.spend_upper = ad_data["spend_upper"]
            updated_count += 1

            ad_data["id"] = str(existing.id)
            ads_with_ids.append(ad_data)
        else:
            ad_id = uuid.uuid4()
            ad = Ad(
                id=ad_id,
                platform=platform,
                platform_ad_id=platform_ad_id,
                advertiser_id=ad_data.get("advertiser_id"),
                advertiser_name=ad_data.get("advertiser_name"),
                advertiser_page_url=ad_data.get("advertiser_page_url"),
                ad_type=ad_data.get("ad_type", "image"),
                headline=ad_data.get("headline"),
                body_text=ad_data.get("body_text"),
                cta_type=ad_data.get("cta_type"),
                media_urls=ad_data.get("media_urls", []),
                media_s3_keys=ad_data.get("media_s3_keys", []),
                thumbnail_url=ad_data.get("thumbnail_url"),
                landing_page_url=ad_data.get("landing_page_url"),
                target_countries=ad_data.get("target_countries", []),
                target_age_min=ad_data.get("target_age_min"),
                target_age_max=ad_data.get("target_age_max"),
                target_gender=ad_data.get("target_gender"),
                target_interests=ad_data.get("target_interests", []),
                impressions_lower=ad_data.get("impressions_lower"),
                impressions_upper=ad_data.get("impressions_upper"),
                spend_lower=ad_data.get("spend_lower"),
                spend_upper=ad_data.get("spend_upper"),
                likes=ad_data.get("likes", 0),
                comments=ad_data.get("comments", 0),
                shares=ad_data.get("shares", 0),
                language=ad_data.get("language"),
                category=ad_data.get("category"),
                tags=ad_data.get("tags", []),
                sentiment=ad_data.get("sentiment"),
                first_seen=_to_datetime(ad_data.get("first_seen")),
                last_seen=_to_datetime(ad_data.get("last_seen")),
                is_active=ad_data.get("is_active", True),
                collection_count=1,
                content_hash=content_hash,
            )
            db.add(ad)
            new_count += 1

            ad_data["id"] = str(ad_id)
            ads_with_ids.append(ad_data)

    await db.commit()

    logger.info(f"Upsert: {new_count} new, {updated_count} updated")
    return {"new": new_count, "updated": updated_count, "ads": ads_with_ids}


async def index_ads_to_es(es, ads: list[dict]) -> int:
    """Bulk index ads into Elasticsearch. Returns count indexed."""
    if not ads:
        return 0
    await bulk_index_ads(es, ads)
    logger.info(f"Indexed {len(ads)} ads to Elasticsearch")
    return len(ads)
