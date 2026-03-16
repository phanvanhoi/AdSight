"""
Cross-platform advertiser matching.
Match same brand across Meta, TikTok, Google by name, URL, and creative similarity.
"""

import logging
import re
import unicodedata
from urllib.parse import urlparse

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.advertiser_group import AdvertiserGroup

logger = logging.getLogger(__name__)


def normalize_advertiser_name(name: str) -> str:
    """Normalize name for comparison: lowercase, remove common suffixes."""
    if not name:
        return ""
    name = unicodedata.normalize("NFC", name).lower().strip()
    for suffix in [" official", " vn", " vietnam", " shop", " store",
                   " chính hãng", " - ", " | "]:
        name = name.replace(suffix, "")
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two advertiser names (0-1)."""
    n1 = remove_diacritics(normalize_advertiser_name(name1))
    n2 = remove_diacritics(normalize_advertiser_name(name2))

    if not n1 or not n2:
        return 0.0

    if n1 == n2:
        return 1.0

    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    jaccard = len(intersection) / len(union)

    if n1 in n2 or n2 in n1:
        return max(jaccard, 0.8)

    return jaccard


def extract_domain(url: str | None) -> str | None:
    """Extract domain from URL for matching."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain in ("facebook.com", "tiktok.com", "instagram.com", "google.com"):
            return None
        return domain if domain else None
    except Exception:
        return None


async def match_advertisers(
    db: AsyncSession,
    similarity_threshold: float = 0.7,
    batch_size: int = 100,
) -> dict:
    """
    Find and group advertisers across platforms.
    Returns {"groups_created": N, "ads_matched": M}
    """
    stmt = (
        select(
            Ad.advertiser_name,
            Ad.advertiser_id,
            Ad.platform,
            func.count(Ad.id).label("ad_count"),
            func.sum(Ad.estimated_total_spend).label("total_spend"),
        )
        .where(Ad.advertiser_name.isnot(None), Ad.advertiser_name != "")
        .group_by(Ad.advertiser_name, Ad.advertiser_id, Ad.platform)
        .order_by(func.count(Ad.id).desc())
        .limit(1000)
    )
    result = await db.execute(stmt)
    advertisers = result.all()

    groups_created = 0
    ads_matched = 0

    # Group by normalized name
    name_groups: dict[str, list] = {}
    for adv in advertisers:
        slug = remove_diacritics(normalize_advertiser_name(adv.advertiser_name))
        if not slug:
            continue
        if slug not in name_groups:
            name_groups[slug] = []
        name_groups[slug].append(adv)

    # For name groups with multiple platforms → create AdvertiserGroup
    for slug, members in name_groups.items():
        platforms = set(m.platform for m in members)
        if len(platforms) < 2:
            continue

        existing = await db.execute(
            select(AdvertiserGroup).where(AdvertiserGroup.slug == slug)
        )
        if existing.scalar_one_or_none():
            continue

        platform_ids: dict[str, list] = {}
        total_ads = 0
        total_spend = 0.0
        canonical_name = max(members, key=lambda m: m.ad_count).advertiser_name

        for m in members:
            if m.platform not in platform_ids:
                platform_ids[m.platform] = []
            if m.advertiser_id:
                platform_ids[m.platform].append(m.advertiser_id)
            total_ads += m.ad_count
            total_spend += float(m.total_spend or 0)

        group = AdvertiserGroup(
            name=canonical_name,
            slug=slug,
            platform_ids=platform_ids,
            total_ads=total_ads,
            total_estimated_spend=total_spend,
        )
        db.add(group)
        groups_created += 1
        ads_matched += total_ads

    await db.commit()

    stats = {"groups_created": groups_created, "ads_matched": ads_matched}
    logger.info(f"Advertiser matching complete: {stats}")
    return stats
