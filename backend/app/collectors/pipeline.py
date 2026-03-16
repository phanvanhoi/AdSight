import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.search.indexing import bulk_index_ads

logger = logging.getLogger(__name__)


async def process_ads(
    db: AsyncSession,
    es,
    normalized_ads: list[dict],
) -> int:
    """
    Process normalized ads: deduplicate, store in DB, index in ES.
    Returns count of new ads added.
    """
    new_count = 0
    ads_to_index = []

    for ad_data in normalized_ads:
        platform = ad_data["platform"]
        platform_ad_id = ad_data["platform_ad_id"]

        # Check for existing ad (deduplicate)
        result = await db.execute(
            select(Ad).where(
                Ad.platform == platform,
                Ad.platform_ad_id == platform_ad_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update last_seen and metrics
            existing.last_seen = datetime.now(timezone.utc)
            existing.likes = ad_data.get("likes", existing.likes)
            existing.comments = ad_data.get("comments", existing.comments)
            existing.shares = ad_data.get("shares", existing.shares)
            existing.is_active = ad_data.get("is_active", existing.is_active)

            # Prepare for ES re-index
            ad_data["id"] = str(existing.id)
            ads_to_index.append(ad_data)
        else:
            # Create new ad
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
                first_seen=ad_data.get("first_seen"),
                last_seen=ad_data.get("last_seen"),
                is_active=ad_data.get("is_active", True),
            )
            db.add(ad)
            new_count += 1

            ad_data["id"] = str(ad_id)
            ads_to_index.append(ad_data)

    # Commit DB changes
    await db.commit()

    # Bulk index to Elasticsearch
    if ads_to_index:
        await bulk_index_ads(es, ads_to_index)

    logger.info(f"Pipeline: {new_count} new ads, {len(ads_to_index)} total indexed")
    return new_count
