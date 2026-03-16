"""Tests for enrichment: categorizer (7) + estimator (5) = 12 tests."""

from datetime import datetime, timedelta, timezone

import pytest

from app.enrichment.categorizer import categorize_ad
from app.enrichment.estimator import estimate_ad_metrics


# ===========================================================================
# Categorizer tests (7)
# ===========================================================================
class TestCategorizerBeauty:
    """Test 1: Beauty product with discount."""

    def test_kem_chong_nang_giam_gia(self):
        result = categorize_ad(
            headline="Kem chống nắng SPF50 giảm 50%",
            body_text="Bảo vệ da khỏi tia UV, dưỡng da trắng sáng",
        )
        assert result["category_l1"] == "Mỹ phẩm"
        assert result["category_l2"] == "Kem chống nắng"
        assert "discount" in result["detected_offers"]
        assert any("50%" in m for m in result["detected_offers"]["discount"])


class TestCategorizerFashion:
    """Test 2: Fashion product with price."""

    def test_ao_hoodie_199k(self):
        result = categorize_ad(
            headline="Áo hoodie oversize chỉ 199K",
            body_text="Chất liệu cotton mát mẻ, free size",
        )
        assert result["category_l1"] == "Thời trang"
        assert result["category_l2"] == "Áo"


class TestCategorizerEducation:
    """Test 3: Education with trust triggers."""

    def test_khoa_hoc_ielts(self):
        result = categorize_ad(
            headline="Khóa học IELTS 7.0 cam kết đầu ra",
            body_text="Học tiếng anh với giáo viên bản ngữ, bảo hành kết quả",
        )
        assert result["category_l1"] == "Giáo dục"
        assert result["category_l2"] == "Ngoại ngữ"
        assert "trust" in result["emotional_triggers"]


class TestCategorizerOffers:
    """Test 4: Multiple offer types."""

    def test_flash_sale_combo(self):
        result = categorize_ad(
            headline="Flash sale 12.12 mua 1 tặng 1 freeship",
            body_text="Siêu sale giảm 30% toàn bộ sản phẩm",
        )
        offers = result["detected_offers"]
        assert "discount" in offers
        assert "bundle" in offers
        assert "freeship" in offers
        assert "urgency" in offers


class TestCategorizerEmotionalTriggers:
    """Test 5: Fear + desire triggers."""

    def test_fear_desire(self):
        result = categorize_ad(
            headline="Da xấu lão hóa? Serum retinol giúp bạn",
            body_text="Trắng sáng sau 7 ngày, chính hãng 100%",
        )
        triggers = result["emotional_triggers"]
        assert "fear" in triggers
        assert "desire" in triggers
        assert "trust" in triggers


class TestCategorizerEmpty:
    """Test 6: Empty/None input."""

    def test_none_input(self):
        result = categorize_ad(None, None)
        assert result["category_l1"] is None
        assert result["category_l2"] is None
        assert result["detected_offers"] == {}
        assert result["emotional_triggers"] == {}
        assert result["target_audience_guess"] is None

    def test_empty_strings(self):
        result = categorize_ad("", "")
        assert result["category_l1"] is None


class TestCategorizerMixed:
    """Test 7: Mixed categories — highest count wins."""

    def test_highest_count_wins(self):
        result = categorize_ad(
            headline="Serum dưỡng da collagen vitamin C",
            body_text="Kem chống nắng mặt nạ toner sữa rửa mặt skincare mỹ phẩm. Áo thun.",
        )
        # Beauty has many more keywords than fashion
        assert result["category_l1"] == "Mỹ phẩm"


# ===========================================================================
# Estimator tests (5)
# ===========================================================================
class TestEstimatorMeta:
    """Test 8: Meta ad with spend + impressions."""

    def test_meta_full_data(self):
        now = datetime.now(timezone.utc)
        result = estimate_ad_metrics({
            "platform": "meta",
            "first_seen": now - timedelta(days=10),
            "last_seen": now,
            "spend_lower": 100.0,
            "spend_upper": 200.0,
            "impressions_lower": 5000,
            "impressions_upper": 15000,
            "likes": 300,
            "comments": 50,
            "shares": 20,
        })
        assert result["estimated_total_spend"] == 150.0
        assert result["estimated_daily_spend"] == 15.0
        assert result["cpm_estimate"] is not None
        assert result["cpm_estimate"] == 15.0  # 150/10000*1000
        assert result["engagement_rate"] is not None
        assert result["viral_score"] > 0


class TestEstimatorTikTok:
    """Test 9: TikTok without impressions — likes heuristic."""

    def test_tiktok_no_impressions(self):
        now = datetime.now(timezone.utc)
        result = estimate_ad_metrics({
            "platform": "tiktok",
            "first_seen": now - timedelta(days=5),
            "last_seen": now,
            "spend_lower": None,
            "spend_upper": None,
            "impressions_lower": None,
            "impressions_upper": None,
            "likes": 1000,
            "comments": 100,
            "shares": 50,
        })
        assert result["estimated_total_spend"] is None
        assert result["cpm_estimate"] is None
        # Engagement rate via heuristic: (1000+100+50) / (1000*15)
        assert result["engagement_rate"] is not None
        assert round(result["engagement_rate"], 4) == round(1150 / 15000, 4)


class TestEstimatorHot:
    """Test 10: Hot ad — high engagement, recent, short run."""

    def test_is_hot_true(self):
        now = datetime.now(timezone.utc)
        result = estimate_ad_metrics({
            "platform": "tiktok",
            "first_seen": now - timedelta(days=1),
            "last_seen": now,
            "spend_lower": None,
            "spend_upper": None,
            "impressions_lower": None,
            "impressions_upper": None,
            "likes": 5000,
            "comments": 500,
            "shares": 200,
        })
        assert result["viral_score"] > 70
        assert result["is_hot"] is True


class TestEstimatorCold:
    """Test 11: Cold ad — low engagement, long run."""

    def test_is_hot_false(self):
        now = datetime.now(timezone.utc)
        result = estimate_ad_metrics({
            "platform": "meta",
            "first_seen": now - timedelta(days=30),
            "last_seen": now - timedelta(days=15),
            "spend_lower": 10.0,
            "spend_upper": 20.0,
            "impressions_lower": 1000,
            "impressions_upper": 3000,
            "likes": 50,
            "comments": 10,
            "shares": 5,
        })
        assert result["is_hot"] is False


class TestEstimatorAllNone:
    """Test 12: All None input."""

    def test_all_none(self):
        result = estimate_ad_metrics({
            "platform": "meta",
            "first_seen": None,
            "last_seen": None,
            "spend_lower": None,
            "spend_upper": None,
            "impressions_lower": None,
            "impressions_upper": None,
            "likes": None,
            "comments": None,
            "shares": None,
        })
        assert result["estimated_daily_spend"] is None
        assert result["estimated_total_spend"] is None
        assert result["cpm_estimate"] is None
        assert result["viral_score"] == 0.0 or result["viral_score"] >= 0
        assert result["is_hot"] is False
