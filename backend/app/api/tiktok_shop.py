from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tiktok_shop import TikTokShop, TikTokShopProduct

router = APIRouter()


@router.get("/products")
async def search_products(
    q: str = "",
    category: str | None = None,
    min_sales: int | None = None,
    max_price: float | None = None,
    sort: str = "sales",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search TikTok Shop products."""
    stmt = select(TikTokShopProduct)

    if q:
        stmt = stmt.where(TikTokShopProduct.product_name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(TikTokShopProduct.category == category)
    if min_sales is not None:
        stmt = stmt.where(TikTokShopProduct.sales_count >= min_sales)
    if max_price is not None:
        stmt = stmt.where(TikTokShopProduct.price <= max_price)

    # Sort
    if sort == "price":
        stmt = stmt.order_by(TikTokShopProduct.price.asc())
    elif sort == "revenue":
        stmt = stmt.order_by(desc(TikTokShopProduct.estimated_daily_revenue))
    elif sort == "rating":
        stmt = stmt.order_by(desc(TikTokShopProduct.rating))
    else:  # sales
        stmt = stmt.order_by(desc(TikTokShopProduct.sales_count))

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [
            {
                "id": str(p.id),
                "product_id": p.product_id,
                "product_name": p.product_name,
                "price": p.price,
                "original_price": p.original_price,
                "sales_count": p.sales_count,
                "rating": p.rating,
                "category": p.category,
                "estimated_daily_revenue": p.estimated_daily_revenue,
            }
            for p in products
        ],
    }


@router.get("/products/{product_id}")
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """Get product detail with sales history."""
    result = await db.execute(
        select(TikTokShopProduct).where(TikTokShopProduct.product_id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": str(product.id),
        "product_id": product.product_id,
        "product_name": product.product_name,
        "product_url": product.product_url,
        "price": product.price,
        "original_price": product.original_price,
        "sales_count": product.sales_count,
        "review_count": product.review_count,
        "rating": product.rating,
        "category": product.category,
        "images": product.images,
        "daily_sales": product.daily_sales,
        "estimated_daily_revenue": product.estimated_daily_revenue,
        "estimated_monthly_revenue": product.estimated_monthly_revenue,
    }


@router.get("/shops/{shop_id}")
async def get_shop(shop_id: str, db: AsyncSession = Depends(get_db)):
    """Get shop detail with products."""
    result = await db.execute(
        select(TikTokShop).where(TikTokShop.shop_id == shop_id)
    )
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    products_result = await db.execute(
        select(TikTokShopProduct)
        .where(TikTokShopProduct.shop_id_fk == shop.id)
        .order_by(desc(TikTokShopProduct.sales_count))
        .limit(50)
    )
    products = products_result.scalars().all()

    return {
        "id": str(shop.id),
        "shop_id": shop.shop_id,
        "shop_name": shop.shop_name,
        "followers": shop.followers,
        "rating": shop.rating,
        "total_products": shop.total_products,
        "is_verified": shop.is_verified,
        "products": [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "price": p.price,
                "sales_count": p.sales_count,
            }
            for p in products
        ],
    }


@router.get("/trending")
async def trending_products(
    period: str = "7d",
    category: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get trending products by sales velocity."""
    stmt = (
        select(TikTokShopProduct)
        .where(TikTokShopProduct.estimated_daily_revenue.isnot(None))
    )

    if category:
        stmt = stmt.where(TikTokShopProduct.category == category)

    stmt = stmt.order_by(desc(TikTokShopProduct.estimated_daily_revenue)).limit(limit)

    result = await db.execute(stmt)
    products = result.scalars().all()

    return {
        "period": period,
        "results": [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "price": p.price,
                "sales_count": p.sales_count,
                "estimated_daily_revenue": p.estimated_daily_revenue,
                "category": p.category,
            }
            for p in products
        ],
    }
