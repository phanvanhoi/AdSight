"""
Download ad creatives (images/videos) to S3, extract metadata, compute perceptual hash.
"""

import asyncio
import io
import logging
from collections import Counter
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


def analyze_image(image_bytes: bytes) -> dict:
    """Analyze image: dimensions, format, colors, text overlay detection, phash."""
    from PIL import Image
    import imagehash

    img = Image.open(io.BytesIO(image_bytes))

    # Perceptual hash
    phash = str(imagehash.phash(img, hash_size=16))

    # Dominant colors
    small = img.copy().resize((50, 50)).convert("RGB")
    pixels = list(small.getdata())
    color_counts = Counter(pixels)
    top_colors = [f"#{r:02x}{g:02x}{b:02x}" for (r, g, b), _ in color_counts.most_common(3)]

    # Text overlay heuristic: high contrast regions suggest text
    grayscale = img.convert("L")
    histogram = grayscale.histogram()
    very_dark = sum(histogram[:30])
    very_light = sum(histogram[226:])
    total_pixels = img.width * img.height
    has_text = (very_dark + very_light) / total_pixels > 0.15 if total_pixels > 0 else False

    return {
        "width": img.width,
        "height": img.height,
        "format": (img.format or "unknown").lower(),
        "phash": phash,
        "dominant_colors": top_colors,
        "has_text_overlay": has_text,
    }


async def download_and_analyze_creative(
    ad: Ad,
    client: httpx.AsyncClient,
) -> dict | None:
    """
    Download creative from media_urls or thumbnail_url, upload to S3, analyze.
    Returns dict of metadata or None if failed.
    """
    from app.core.storage import upload_file

    urls_to_try = []
    if ad.thumbnail_url:
        urls_to_try.append(ad.thumbnail_url)
    if ad.media_urls and isinstance(ad.media_urls, list):
        urls_to_try.extend(ad.media_urls)

    if not urls_to_try:
        return None

    for url in urls_to_try:
        try:
            response = await client.get(url, follow_redirects=True, timeout=15)
            if response.status_code != 200:
                continue

            content_type = response.headers.get("content-type", "")
            content_bytes = response.content
            file_size = len(content_bytes)

            is_video = "video" in content_type or url.endswith((".mp4", ".webm", ".mov"))
            is_image = "image" in content_type or url.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))

            if is_video and file_size > MAX_VIDEO_SIZE:
                continue
            if is_image and file_size > MAX_IMAGE_SIZE:
                continue

            # Upload to S3
            date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            ext = "mp4" if is_video else "jpg"
            s3_key = f"creatives/{date_prefix}/{ad.platform}_{ad.platform_ad_id}.{ext}"

            await upload_file(content_bytes, s3_key, content_type)

            result = {
                "creative_s3_key": s3_key,
                "creative_file_size": file_size,
                "creative_format": ext,
            }

            if is_image:
                try:
                    analysis = analyze_image(content_bytes)
                    result.update({
                        "creative_width": analysis["width"],
                        "creative_height": analysis["height"],
                        "creative_format": analysis["format"],
                        "creative_phash": analysis["phash"],
                        "dominant_colors": analysis["dominant_colors"],
                        "has_text_overlay": analysis["has_text_overlay"],
                    })
                except Exception as e:
                    logger.warning(f"Image analysis failed: {e}")

            if is_video:
                result["creative_duration"] = None
                result["creative_width"] = None
                result["creative_height"] = None

            return result

        except Exception as e:
            logger.warning(f"Download failed for {url}: {e}")
            continue

    return None


async def download_creatives(
    db: AsyncSession,
    batch_size: int = 20,
    max_total: int = 100,
) -> dict:
    """Download creatives for ads that haven't been processed yet."""
    stmt = (
        select(Ad)
        .where(
            Ad.creative_s3_key.is_(None),
            (Ad.thumbnail_url.isnot(None)) | (Ad.media_urls.isnot(None)),
        )
        .limit(max_total)
    )
    result = await db.execute(stmt)
    ads = result.scalars().all()

    if not ads:
        return {"processed": 0, "downloaded": 0, "failed": 0}

    downloaded = 0
    failed = 0

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 AdSight Bot/1.0"},
    ) as client:
        for i in range(0, len(ads), batch_size):
            batch = ads[i:i + batch_size]

            for ad in batch:
                creative_data = await download_and_analyze_creative(ad, client)

                if creative_data:
                    for key, value in creative_data.items():
                        setattr(ad, key, value)
                    downloaded += 1
                else:
                    failed += 1

            await db.commit()
            logger.info(f"Creative batch {i // batch_size + 1}: {len(batch)} ads processed")

    stats = {"processed": len(ads), "downloaded": downloaded, "failed": failed}
    logger.info(f"Creative download complete: {stats}")
    return stats
