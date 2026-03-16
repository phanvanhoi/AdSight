"""Tests for TikTok Shop crawler — 9 tests."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.collectors.tiktok_shop_crawler import normalize_product, upsert_products
from app.models.tiktok_shop import TikTokShop, TikTokShopProduct


class TestNormalizeProduct:
    def test_full_response(self):
        raw = {
            "product_id": "prod_001",
            "product_name": "Kem chống nắng SPF50",
            "product_url": "https://shop.tiktok.com/prod_001",
            "price": 19900000,  # cents
            "original_price": 29900000,
            "sales_count": 1500,
            "review_count": 200,
            "rating": 4.8,
            "category_name": "Làm đẹp",
            "images": ["img1.jpg", "img2.jpg"],
            "shop_id": "shop_001",
            "shop_name": "Beauty VN",
        }
        result = normalize_product(raw)
        assert result["product_id"] == "prod_001"
        assert result["product_name"] == "Kem chống nắng SPF50"
        assert result["price"] == 199000.0
        assert result["original_price"] == 299000.0
        assert result["sales_count"] == 1500
        assert result["shop_id"] == "shop_001"

    def test_price_conversion(self):
        raw = {"product_id": "p1", "price": 5000000, "original_price": 0}
        result = normalize_product(raw)
        assert result["price"] == 50000.0
        assert result["original_price"] is None  # 0 → None

    def test_missing_fields_defaults(self):
        raw = {"id": "p2", "title": "Test Product"}
        result = normalize_product(raw)
        assert result["product_id"] == "p2"
        assert result["product_name"] == "Test Product"
        assert result["price"] == 0.0
        assert result["sales_count"] == 0
        assert result["is_active"] is True


class TestUpsertProducts:
    @pytest.mark.asyncio
    async def test_insert_new(self, db):
        products = [
            {
                "product_id": "new_001",
                "product_name": "Test Product",
                "product_url": "https://shop.tiktok.com/new_001",
                "price": 199000.0,
                "original_price": None,
                "sales_count": 100,
                "review_count": 10,
                "rating": 4.5,
                "category": "Làm đẹp",
                "images": [],
                "shop_id": "shop_new_001",
                "shop_name": "Test Shop",
            }
        ]
        result = await upsert_products(db, products)
        assert result["new_products"] == 1
        assert result["shops_created"] == 1

    @pytest.mark.asyncio
    async def test_update_existing_sales_delta(self, db):
        # Insert shop first
        shop = TikTokShop(shop_id="shop_u1", shop_name="Shop U1")
        db.add(shop)
        await db.flush()

        # Insert product
        product = TikTokShopProduct(
            product_id="upd_001",
            product_name="Existing Product",
            price=100000.0,
            sales_count=500,
            review_count=50,
            shop_id_fk=shop.id,
            daily_sales=[],
        )
        db.add(product)
        await db.commit()

        # Update with higher sales
        products = [
            {
                "product_id": "upd_001",
                "product_name": "Existing Product",
                "price": 100000.0,
                "original_price": None,
                "sales_count": 650,  # +150
                "review_count": 60,
                "rating": 4.6,
                "category": "Test",
                "images": [],
                "shop_id": "shop_u1",
                "shop_name": "Shop U1",
            }
        ]
        result = await upsert_products(db, products)
        assert result["updated_products"] == 1

        # Check daily_sales was appended
        from sqlalchemy import select
        res = await db.execute(
            select(TikTokShopProduct).where(TikTokShopProduct.product_id == "upd_001")
        )
        updated = res.scalar_one()
        assert len(updated.daily_sales) == 1
        assert updated.daily_sales[0]["sales_delta"] == 150

    @pytest.mark.asyncio
    async def test_revenue_estimation(self, db):
        shop = TikTokShop(shop_id="shop_rev", shop_name="Revenue Shop")
        db.add(shop)
        await db.flush()

        product = TikTokShopProduct(
            product_id="rev_001",
            product_name="Revenue Product",
            price=50000.0,
            sales_count=1000,
            review_count=100,
            shop_id_fk=shop.id,
            daily_sales=[],
        )
        db.add(product)
        await db.commit()

        products = [
            {
                "product_id": "rev_001",
                "product_name": "Revenue Product",
                "price": 50000.0,
                "original_price": None,
                "sales_count": 1200,  # +200 delta
                "review_count": 120,
                "rating": 4.5,
                "category": "Test",
                "images": [],
                "shop_id": "shop_rev",
                "shop_name": "Revenue Shop",
            }
        ]
        result = await upsert_products(db, products)

        from sqlalchemy import select
        res = await db.execute(
            select(TikTokShopProduct).where(TikTokShopProduct.product_id == "rev_001")
        )
        updated = res.scalar_one()
        # delta=200, price=50000 → daily_revenue = 10,000,000
        assert updated.estimated_daily_revenue == 200 * 50000.0
        assert updated.estimated_monthly_revenue == 200 * 50000.0 * 30


class TestFetchProducts:
    @pytest.mark.asyncio
    async def test_mock_fetch(self):
        from app.collectors.tiktok_shop_crawler import fetch_products

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "products": [
                    {"product_id": "1", "product_name": "Prod 1", "price": 10000},
                    {"product_id": "2", "product_name": "Prod 2", "price": 20000},
                ]
            }
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with patch("app.collectors.tiktok_shop_crawler.asyncio.sleep", new_callable=AsyncMock):
                products = await fetch_products(keyword="test", max_pages=1)

        assert len(products) == 2

    @pytest.mark.asyncio
    async def test_403_stops(self):
        from app.collectors.tiktok_shop_crawler import fetch_products

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            products = await fetch_products(keyword="test", max_pages=3)

        assert len(products) == 0
