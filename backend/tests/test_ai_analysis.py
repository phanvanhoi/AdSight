"""Tests for AI creative analysis."""
import uuid

import pytest
from unittest.mock import patch
from httpx import AsyncClient

from tests.conftest import make_auth_headers


@pytest.mark.asyncio
class TestAIAnalysisEndpoint:
    async def test_ai_analysis_free_user_403(
        self, async_client: AsyncClient, test_user, sample_ad
    ):
        """Free user cannot use AI analysis."""
        headers = make_auth_headers(test_user)
        resp = await async_client.post(
            f"/api/ads/{sample_ad.id}/ai-analysis", headers=headers
        )
        assert resp.status_code == 403

    async def test_ai_analysis_nonexistent_ad_404(
        self, async_client: AsyncClient, pro_user
    ):
        """404 for non-existent ad."""
        headers = make_auth_headers(pro_user)
        resp = await async_client.post(
            f"/api/ads/{uuid.uuid4()}/ai-analysis", headers=headers
        )
        assert resp.status_code == 404

    @patch("app.api.ads.analyze_ad_creative")
    async def test_ai_analysis_success(
        self, mock_analyze, async_client: AsyncClient, pro_user, sample_ad
    ):
        """Pro user gets AI analysis and credit is consumed."""
        mock_analyze.return_value = {
            "summary": "Test analysis",
            "hook_analysis": {"hook_type": "question", "effectiveness": 7},
            "strengths": ["Good headline"],
            "weaknesses": ["No CTA"],
            "suggestions": ["Add urgency"],
        }
        headers = make_auth_headers(pro_user)
        resp = await async_client.post(
            f"/api/ads/{sample_ad.id}/ai-analysis", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached"] is False
        assert "analysis" in data
        mock_analyze.assert_awaited_once()

    @patch("app.api.ads.analyze_ad_creative")
    async def test_ai_analysis_cached(
        self, mock_analyze, async_client: AsyncClient, pro_user, sample_ad, db
    ):
        """Returns cached analysis if < 7 days old."""
        from datetime import datetime, timezone

        sample_ad.ai_analysis = {"summary": "Cached"}
        sample_ad.ai_analyzed_at = datetime.now(timezone.utc)
        await db.commit()

        headers = make_auth_headers(pro_user)
        resp = await async_client.post(
            f"/api/ads/{sample_ad.id}/ai-analysis", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["cached"] is True
        mock_analyze.assert_not_awaited()

    async def test_ai_credits_exhausted_429(
        self, async_client: AsyncClient, pro_user, sample_ad, db
    ):
        """Pro user with 50 credits used gets 429."""
        from datetime import datetime, timezone

        pro_user.ai_credits_used = 50
        pro_user.ai_credits_reset = datetime.now(timezone.utc)
        await db.commit()

        headers = make_auth_headers(pro_user)
        resp = await async_client.post(
            f"/api/ads/{sample_ad.id}/ai-analysis", headers=headers
        )
        assert resp.status_code == 429


class TestCategorizer:
    def test_categorize_my_pham(self):
        """Mỹ phẩm category detection."""
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad("Kem chống nắng SPF50", "Bảo vệ da khỏi tia UV")
        assert result["category_l1"] == "Mỹ phẩm"
        assert result["category_l2"] == "Kem chống nắng"

    def test_categorize_cong_nghe(self):
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad("iPhone 16 Pro Max", "Mua smartphone chính hãng")
        assert result["category_l1"] == "Công nghệ"
        assert result["category_l2"] == "Điện thoại"

    def test_categorize_du_lich(self):
        """Du lịch L1 category."""
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad("Tour Đà Nẵng 3N2D", "Khách sạn 5 sao resort")
        assert result["category_l1"] == "Du lịch"

    def test_categorize_xe_co(self):
        """Xe cộ L1 category with subcategory."""
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad("Honda Winner X", "Xe máy Honda chính hãng")
        assert result["category_l1"] == "Xe cộ"
        assert result["category_l2"] == "Xe máy"

    def test_offer_detection(self):
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad("Sale 50%", "Giảm 50% free ship mua 2 tặng 1")
        offers = result["detected_offers"]
        assert "discount" in offers
        assert "freeship" in offers
        assert "bundle" in offers

    def test_emotional_triggers(self):
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad("", "Da xấu lão hóa? Kem dưỡng chính hãng cam kết trắng sáng")
        triggers = result["emotional_triggers"]
        assert "fear" in triggers
        assert "trust" in triggers
        assert "desire" in triggers

    def test_empty_input(self):
        from app.enrichment.categorizer import categorize_ad

        result = categorize_ad(None, None)
        assert result["category_l1"] is None
