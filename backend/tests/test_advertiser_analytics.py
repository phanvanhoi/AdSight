"""Tests for advertiser analytics endpoint."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.advertiser_group import AdvertiserGroup


@pytest.mark.asyncio
class TestAdvertiserAnalytics:
    async def test_analytics_not_found(self, async_client: AsyncClient):
        resp = await async_client.get(f"/api/advertisers/{uuid.uuid4()}/analytics")
        assert resp.status_code == 404

    async def test_analytics_empty_group(
        self, async_client: AsyncClient, db: AsyncSession
    ):
        group = AdvertiserGroup(
            name="Empty Group",
            slug="empty-group",
            platform_ids={},
            total_ads=0,
            total_estimated_spend=0,
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)

        resp = await async_client.get(f"/api/advertisers/{group.id}/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform_breakdown"] == {}
        assert data["ads_timeline"] == []
        assert data["top_ads"] == []
        assert data["total_active_ads"] == 0

    async def test_analytics_response_shape(
        self, async_client: AsyncClient, db: AsyncSession
    ):
        """Verify all expected keys in analytics response."""
        group = AdvertiserGroup(
            name="Test Group",
            slug="test-group-analytics",
            platform_ids={},
            total_ads=0,
            total_estimated_spend=0,
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)

        resp = await async_client.get(f"/api/advertisers/{group.id}/analytics")
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = [
            "platform_breakdown", "ads_timeline", "category_breakdown",
            "top_ads", "ad_type_breakdown", "avg_engagement_rate",
            "avg_viral_score", "total_active_ads", "first_ad_date", "latest_ad_date",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
