"""
Enrichment Pipeline — orchestrates categorizer + estimator on ads.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.categorizer import categorize_ad
from app.enrichment.estimator import estimate_ad_metrics
from app.models.ad import Ad

logger = logging.getLogger(__name__)


async def enrich_ads(db: AsyncSession, ad_ids: list[str] | None = None, batch_size: int = 100) -> dict:
    """
    Enrich ads with categorization + spend metrics.

    Args:
        db: Database session.
        ad_ids: If provided, only enrich these ads. Otherwise enrich unenriched.
        batch_size: Number of ads to process per batch.

    Returns:
        {"enriched": N, "skipped": M}
    """
    if ad_ids:
        query = select(Ad).where(Ad.id.in_(ad_ids))
    else:
        query = select(Ad).where(Ad.category_l1.is_(None)).limit(batch_size)

    result = await db.execute(query)
    ads = result.scalars().all()

    enriched = 0
    skipped = 0

    for ad in ads:
        try:
            _enrich_single(ad)
            enriched += 1
        except Exception as e:
            logger.warning(f"Failed to enrich ad {ad.id}: {e}")
            skipped += 1

    await db.commit()

    logger.info(f"Enrichment: {enriched} enriched, {skipped} skipped")
    return {"enriched": enriched, "skipped": skipped}


async def enrich_new_ads(db: AsyncSession) -> dict:
    """Enrich only unenriched ads (category_l1 IS NULL)."""
    return await enrich_ads(db, ad_ids=None, batch_size=500)


def _enrich_single(ad: Ad) -> None:
    """Apply categorizer + estimator to a single Ad ORM object."""
    # Categorize
    cat_result = categorize_ad(ad.headline, ad.body_text)
    ad.category_l1 = cat_result["category_l1"]
    ad.category_l2 = cat_result["category_l2"]
    ad.detected_offers = cat_result["detected_offers"]
    ad.emotional_triggers = cat_result["emotional_triggers"]
    ad.target_audience_guess = cat_result["target_audience_guess"]

    # Estimate metrics
    ad_data = {
        "first_seen": ad.first_seen,
        "last_seen": ad.last_seen,
        "spend_lower": ad.spend_lower,
        "spend_upper": ad.spend_upper,
        "impressions_lower": ad.impressions_lower,
        "impressions_upper": ad.impressions_upper,
        "likes": ad.likes,
        "comments": ad.comments,
        "shares": ad.shares,
        "platform": ad.platform,
    }
    est_result = estimate_ad_metrics(ad_data)
    ad.estimated_daily_spend = est_result["estimated_daily_spend"]
    ad.estimated_total_spend = est_result["estimated_total_spend"]
    ad.cpm_estimate = est_result["cpm_estimate"]
    ad.engagement_rate = est_result["engagement_rate"]
    ad.viral_score = est_result["viral_score"]
    ad.is_hot = est_result["is_hot"]
