"""Tests for email HTML templates."""
from app.core.email_templates import competitor_alert_email, daily_digest_email


class TestCompetitorAlertEmail:
    def test_renders_html(self):
        html = competitor_alert_email(
            alert_name="Test Alert",
            match_value="Shopee",
            ad_count=3,
            ads_preview=[
                {"headline": "Ad 1", "platform": "meta", "ad_type": "image", "first_seen": "2026-03-15"},
            ],
        )
        assert "<!DOCTYPE html>" in html
        assert "Test Alert" in html
        assert "Shopee" in html
        assert "META" in html

    def test_extra_note_over_5(self):
        html = competitor_alert_email("Alert", "test", 10, [])
        assert "5 ads" in html

    def test_no_extra_under_5(self):
        html = competitor_alert_email("Alert", "test", 3, [])
        assert "ads khác" not in html


class TestDailyDigestEmail:
    def test_renders_html(self):
        html = daily_digest_email(
            user_name="Nguyễn Văn A",
            date_str="17/03/2026",
            trending_ads=[
                {"headline": "Trending Ad", "platform": "meta", "likes": 5000, "viral_score": 85, "id": "1"},
            ],
            competitor_updates=[
                {"alert_name": "Shopee", "count": 5},
            ],
            stats={"total_new_ads": 150, "top_category": "Mỹ phẩm", "most_active_platform": "meta"},
        )
        assert "<!DOCTYPE html>" in html
        assert "Nguyễn Văn A" in html
        assert "17/03/2026" in html
        assert "Trending Ad" in html
        assert "Shopee" in html
        assert "150" in html

    def test_no_competitor_section_when_empty(self):
        html = daily_digest_email(
            user_name="Test",
            date_str="17/03/2026",
            trending_ads=[],
            competitor_updates=[],
            stats={"total_new_ads": 0, "top_category": "N/A", "most_active_platform": "N/A"},
        )
        assert "Cập nhật đối thủ" not in html

    def test_likes_formatting(self):
        html = daily_digest_email(
            user_name="Test",
            date_str="17/03/2026",
            trending_ads=[
                {"headline": "Ad", "platform": "meta", "likes": 2500, "viral_score": 50, "id": "1"},
            ],
            competitor_updates=[],
            stats={"total_new_ads": 10, "top_category": "N/A", "most_active_platform": "N/A"},
        )
        assert "2.5K" in html
