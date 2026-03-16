"""
Landing page crawler.
Crawls ad landing pages to extract product info, platform detection, trust signals.
Uses httpx for lightweight crawling (no Playwright dependency required at runtime).
Falls back gracefully when Playwright is not installed.
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.landing_page import LandingPageInfo

logger = logging.getLogger(__name__)

# Platform detection rules
PLATFORM_PATTERNS = {
    "shopee": [r"shopee\.vn", r"shopee\.co"],
    "lazada": [r"lazada\.vn", r"lazada\.co"],
    "tiktok_shop": [r"shop\.tiktok\.com", r"tiktokshop"],
    "haravan": [r"\.haravan\.com", r"\.myharavan\.com"],
    "sapo": [r"\.sapoweb\.com", r"\.sapo\.vn"],
    "kiotviet": [r"\.kiotviet\.vn"],
    "shopify": [r"\.myshopify\.com", r"cdn\.shopify\.com"],
    "woocommerce": [r"wp-content.*woocommerce", r"wc-ajax"],
    "wordpress": [r"wp-content", r"wp-includes"],
}

# Pixel detection patterns
PIXEL_PATTERNS = {
    "fb_pixel": [r"fbq\s*\(", r"facebook\.com/tr", r"connect\.facebook\.net/.*fbevents"],
    "tiktok_pixel": [r"ttq\.track", r"analytics\.tiktok\.com", r"ttq\.load"],
    "google_analytics": [r"gtag\s*\(", r"google-analytics\.com", r"googletagmanager\.com", r"ga\s*\(\s*'create'"],
}

# Chat widget detection
CHAT_PATTERNS = {
    "zalo": [r"zalo\.me", r"chat\.zalo", r"zalo-chat"],
    "messenger": [r"m\.me/", r"messenger\.com", r"fb-messenger", r"facebook\.com/plugins/customerchat"],
    "tawk": [r"tawk\.to", r"embed\.tawk"],
    "livechat": [r"livechat", r"livechatinc\.com"],
}

# Price extraction patterns (Vietnamese)
PRICE_PATTERNS = [
    r"(\d{1,3}(?:\.\d{3})+)\s*(?:₫|đ|VND|vnđ)",
    r"(\d{1,3}(?:,\d{3})+)\s*(?:₫|đ|VND|vnđ)",
    r"(\d+)\s*[kK]\b",
    r"(?:giá|price|chỉ|còn)\s*:?\s*(\d{1,3}(?:[.,]\d{3})*)",
]


def detect_platform(url: str, page_source: str) -> str:
    """Detect e-commerce platform from URL and page source."""
    url_lower = url.lower()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return platform
            if re.search(pattern, page_source[:5000], re.IGNORECASE):
                return platform
    return "custom"


def detect_pixels(page_source: str) -> dict:
    """Detect tracking pixels in page source."""
    result = {}
    for pixel_name, patterns in PIXEL_PATTERNS.items():
        result[pixel_name] = any(
            re.search(p, page_source, re.IGNORECASE) for p in patterns
        )
    return result


def detect_chat_widget(page_source: str) -> str | None:
    """Detect chat widget type."""
    for widget, patterns in CHAT_PATTERNS.items():
        if any(re.search(p, page_source, re.IGNORECASE) for p in patterns):
            return widget
    return None


def extract_price(page_source: str) -> float | None:
    """Extract product price from page source."""
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, page_source, re.IGNORECASE)
        if match:
            price_str = match.group(1)
            price_str = price_str.replace(".", "").replace(",", "")
            try:
                price = float(price_str)
                if "k" in pattern.lower() and price < 10000:
                    price *= 1000
                if 1000 <= price <= 999_000_000:
                    return price
            except ValueError:
                continue
    return None


def extract_product_name(page_source: str) -> str | None:
    """Extract product name from meta tags or title."""
    match = re.search(r'property="og:title"\s+content="([^"]+)"', page_source)
    if not match:
        match = re.search(r'content="([^"]+)"\s+property="og:title"', page_source)
    if match:
        return match.group(1)[:500]
    match = re.search(r"<title>([^<]+)</title>", page_source, re.IGNORECASE)
    if match:
        return match.group(1).strip()[:500]
    return None


def extract_product_image(page_source: str) -> str | None:
    """Extract product image from meta tags."""
    match = re.search(r'property="og:image"\s+content="([^"]+)"', page_source)
    if not match:
        match = re.search(r'content="([^"]+)"\s+property="og:image"', page_source)
    if match:
        return match.group(1)
    return None


async def crawl_single_page(url: str, client: httpx.AsyncClient) -> dict:
    """Crawl a single landing page using httpx."""
    result = {
        "final_url": url,
        "redirect_chain": [],
        "platform_detected": "custom",
        "product_name": None,
        "product_price": None,
        "product_currency": "VND",
        "product_image_url": None,
        "has_fb_pixel": False,
        "has_tiktok_pixel": False,
        "has_google_analytics": False,
        "has_chat_widget": None,
        "has_ssl": url.startswith("https"),
        "page_load_ms": None,
        "crawl_status": "pending",
        "error_message": None,
    }

    try:
        start_time = time.time()
        response = await client.get(url, follow_redirects=True, timeout=15)
        load_time = int((time.time() - start_time) * 1000)

        result["page_load_ms"] = load_time
        result["final_url"] = str(response.url)
        result["has_ssl"] = str(response.url).startswith("https")

        # Track redirect chain
        result["redirect_chain"] = [str(r.url) for r in response.history] if response.history else [url]

        page_source = response.text

        # Platform detection
        result["platform_detected"] = detect_platform(str(response.url), page_source)

        # Pixel detection
        pixels = detect_pixels(page_source)
        result["has_fb_pixel"] = pixels.get("fb_pixel", False)
        result["has_tiktok_pixel"] = pixels.get("tiktok_pixel", False)
        result["has_google_analytics"] = pixels.get("google_analytics", False)

        # Chat widget
        result["has_chat_widget"] = detect_chat_widget(page_source)

        # Product info
        result["product_name"] = extract_product_name(page_source)
        result["product_price"] = extract_price(page_source)
        result["product_image_url"] = extract_product_image(page_source)

        result["crawl_status"] = "success"

    except httpx.TimeoutException:
        result["crawl_status"] = "timeout"
        result["error_message"] = "Request timed out"
    except Exception as e:
        result["crawl_status"] = "error"
        result["error_message"] = str(e)[:500]
        logger.warning(f"Crawl failed for {url}: {e}")

    return result


async def crawl_landing_pages(
    db: AsyncSession,
    batch_size: int = 20,
    max_total: int = 100,
) -> dict:
    """
    Crawl landing pages for ads that haven't been crawled yet.
    Returns {"crawled": N, "success": M, "failed": K}
    """
    stmt = (
        select(Ad)
        .outerjoin(LandingPageInfo, Ad.id == LandingPageInfo.ad_id)
        .where(
            Ad.landing_page_url.isnot(None),
            Ad.landing_page_url != "",
            LandingPageInfo.id.is_(None),
        )
        .limit(max_total)
    )
    result = await db.execute(stmt)
    ads = result.scalars().all()

    if not ads:
        return {"crawled": 0, "success": 0, "failed": 0}

    success = 0
    failed = 0

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        follow_redirects=True,
        timeout=15,
    ) as client:
        for i in range(0, len(ads), batch_size):
            batch = ads[i:i + batch_size]
            tasks = [crawl_single_page(ad.landing_page_url, client) for ad in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for ad, crawl_result in zip(batch, results):
                if isinstance(crawl_result, Exception):
                    crawl_data = {
                        "crawl_status": "error",
                        "error_message": str(crawl_result)[:500],
                    }
                    failed += 1
                else:
                    crawl_data = crawl_result
                    if crawl_data["crawl_status"] == "success":
                        success += 1
                    else:
                        failed += 1

                lp_info = LandingPageInfo(
                    ad_id=ad.id,
                    crawled_at=datetime.now(timezone.utc),
                    final_url=crawl_data.get("final_url"),
                    redirect_chain=crawl_data.get("redirect_chain"),
                    platform_detected=crawl_data.get("platform_detected"),
                    product_name=crawl_data.get("product_name"),
                    product_price=crawl_data.get("product_price"),
                    product_currency=crawl_data.get("product_currency", "VND"),
                    product_image_url=crawl_data.get("product_image_url"),
                    has_fb_pixel=crawl_data.get("has_fb_pixel", False),
                    has_tiktok_pixel=crawl_data.get("has_tiktok_pixel", False),
                    has_google_analytics=crawl_data.get("has_google_analytics", False),
                    has_chat_widget=crawl_data.get("has_chat_widget"),
                    has_ssl=crawl_data.get("has_ssl", False),
                    page_load_ms=crawl_data.get("page_load_ms"),
                    crawl_status=crawl_data.get("crawl_status", "error"),
                    error_message=crawl_data.get("error_message"),
                )
                db.add(lp_info)

            await db.commit()
            logger.info(f"Crawled batch {i // batch_size + 1}: {len(batch)} pages")

            # Politeness delay between batches
            await asyncio.sleep(2)

    stats = {"crawled": len(ads), "success": success, "failed": failed}
    logger.info(f"Landing page crawl complete: {stats}")
    return stats
