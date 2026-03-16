"""
TikTok Shop VN crawler.
Crawls product data, sales metrics, shop info from TikTok Shop.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session
from app.models.tiktok_shop import TikTokShop, TikTokShopProduct

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

TIKTOK_SHOP_API = "https://shop.tiktok.com/api/v1"


def _get_client_kwargs() -> dict:
    """Get httpx client kwargs with optional proxy."""
    kwargs = {
        "timeout": 15,
        "headers": {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json",
            "Accept-Language": "vi-VN,vi;q=0.9",
        },
        "follow_redirects": True,
    }
    if settings.proxy_enabled and settings.proxy_url:
        kwargs["proxy"] = settings.proxy_url
    return kwargs


async def fetch_products(
    keyword: str = "",
    category: str = "",
    country: str = "VN",
    max_pages: int = 5,
    limit: int = 30,
) -> list[dict]:
    """Fetch product listings from TikTok Shop."""
    all_products = []

    async with httpx.AsyncClient(**_get_client_kwargs()) as client:
        for page in range(1, max_pages + 1):
            try:
                params = {
                    "keyword": keyword,
                    "category": category,
                    "country": country,
                    "page": page,
                    "limit": limit,
                    "sort_by": "sales",
                }

                response = await client.get(
                    f"{TIKTOK_SHOP_API}/products/search",
                    params=params,
                )

                if response.status_code == 403:
                    logger.warning("[tiktok_shop] 403 Forbidden — may need proxy rotation")
                    break

                if response.status_code != 200:
                    logger.warning(f"[tiktok_shop] HTTP {response.status_code} on page {page}")
                    break

                data = response.json()
                products = data.get("data", {}).get("products", [])

                if not products:
                    break

                all_products.extend(products)
                logger.info(f"[tiktok_shop] Page {page}: fetched {len(products)} products")

                # Politeness delay
                await asyncio.sleep(random.uniform(2, 5))

            except Exception as e:
                logger.error(f"[tiktok_shop] Error on page {page}: {e}")
                break

    return all_products


def normalize_product(raw: dict) -> dict:
    """Normalize raw TikTok Shop product to internal schema."""
    raw_price = raw.get("price", raw.get("sale_price", 0))
    raw_original = raw.get("original_price", 0)

    # TikTok prices often in cents
    price = float(raw_price) / 100 if raw_price else 0
    original_price = float(raw_original) / 100 if raw_original else None

    return {
        "product_id": str(raw.get("product_id", raw.get("id", ""))),
        "product_name": raw.get("product_name", raw.get("title", "")),
        "product_url": raw.get("product_url", raw.get("url", "")),
        "price": price,
        "original_price": original_price,
        "currency": "VND",
        "sales_count": int(raw.get("sales_count", raw.get("sold", 0))),
        "review_count": int(raw.get("review_count", raw.get("reviews", 0))),
        "rating": float(raw.get("rating", raw.get("star", 0))),
        "category": raw.get("category_name", raw.get("category", "")),
        "images": raw.get("images", raw.get("image_list", [])),
        "is_active": True,
        "shop_id": str(raw.get("shop_id", raw.get("seller_id", ""))),
        "shop_name": raw.get("shop_name", raw.get("seller_name", "")),
    }


async def upsert_products(db: AsyncSession, products: list[dict]) -> dict:
    """Upsert products + shops into PostgreSQL."""
    new_products = 0
    updated_products = 0
    shops_created = 0

    for prod_data in products:
        shop_id_str = prod_data.get("shop_id", "")
        shop = None

        # Upsert shop
        if shop_id_str:
            result = await db.execute(
                select(TikTokShop).where(TikTokShop.shop_id == shop_id_str)
            )
            shop = result.scalar_one_or_none()

            if not shop:
                shop = TikTokShop(
                    shop_id=shop_id_str,
                    shop_name=prod_data.get("shop_name", ""),
                )
                db.add(shop)
                await db.flush()
                shops_created += 1

        # Upsert product
        result = await db.execute(
            select(TikTokShopProduct).where(
                TikTokShopProduct.product_id == prod_data["product_id"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            old_sales = existing.sales_count
            new_sales = prod_data["sales_count"]
            delta = new_sales - old_sales

            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            daily_sales = existing.daily_sales or []
            if delta > 0:
                daily_sales.append({
                    "date": today,
                    "sales_delta": delta,
                    "total_sales": new_sales,
                    "revenue_est": delta * prod_data["price"],
                })
                daily_sales = daily_sales[-90:]

            existing.sales_count = new_sales
            existing.review_count = prod_data["review_count"]
            existing.rating = prod_data["rating"]
            existing.price = prod_data["price"]
            existing.daily_sales = daily_sales
            existing.estimated_daily_revenue = delta * prod_data["price"] if delta > 0 else existing.estimated_daily_revenue
            existing.estimated_monthly_revenue = (existing.estimated_daily_revenue or 0) * 30

            updated_products += 1
        else:
            if not shop:
                logger.warning(f"[tiktok_shop] Skipping product {prod_data['product_id']} — no shop")
                continue
            product = TikTokShopProduct(
                product_id=prod_data["product_id"],
                product_name=prod_data["product_name"],
                product_url=prod_data.get("product_url"),
                price=prod_data["price"],
                original_price=prod_data.get("original_price"),
                sales_count=prod_data["sales_count"],
                review_count=prod_data["review_count"],
                rating=prod_data.get("rating"),
                category=prod_data.get("category"),
                images=prod_data.get("images"),
                shop_id_fk=shop.id,
                daily_sales=[],
            )
            db.add(product)
            new_products += 1

    await db.commit()
    return {"new_products": new_products, "updated_products": updated_products, "shops_created": shops_created}


VN_TIKTOK_SHOP_CATEGORIES = [
    "Làm đẹp", "Thời trang nữ", "Thời trang nam",
    "Điện tử", "Nhà cửa", "Mẹ & Bé",
    "Thực phẩm", "Sức khỏe", "Phụ kiện",
]


async def collect_and_store(categories: list[str] | None = None) -> dict:
    """Full pipeline: fetch → normalize → upsert."""
    cats = categories or VN_TIKTOK_SHOP_CATEGORIES

    total_fetched = 0
    total_new = 0
    total_updated = 0
    total_shops = 0

    for cat in cats:
        try:
            raw_products = await fetch_products(keyword=cat, max_pages=3)
            normalized = [normalize_product(p) for p in raw_products]
            total_fetched += len(normalized)

            if normalized:
                async with async_session() as db:
                    result = await upsert_products(db, normalized)
                    total_new += result["new_products"]
                    total_updated += result["updated_products"]
                    total_shops += result["shops_created"]

                logger.info(f"[tiktok_shop] '{cat}': {result}")

        except Exception as e:
            logger.error(f"[tiktok_shop] Error collecting '{cat}': {e}", exc_info=True)

    stats = {
        "fetched": total_fetched,
        "new_products": total_new,
        "updated_products": total_updated,
        "shops_created": total_shops,
    }
    logger.info(f"[tiktok_shop] Collection complete: {stats}")
    return stats
