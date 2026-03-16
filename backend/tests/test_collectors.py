"""Tests for Meta and TikTok collectors, upsert logic, and retry handling."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.collectors.base import upsert_ads, index_ads_to_es
from app.collectors.meta_collector import MetaCollector, RateLimitError
from app.collectors.tiktok_collector import TikTokCollector


# ---------------------------------------------------------------------------
# Sample raw API responses
# ---------------------------------------------------------------------------
SAMPLE_META_RAW = {
    "id": "meta_ad_001",
    "page_id": "123456789",
    "page_name": "Shop Thoi Trang VN",
    "ad_creative_bodies": ["Giam gia 50% tat ca san pham"],
    "ad_creative_link_titles": ["Flash Sale Mua He"],
    "ad_creative_link_captions": ["Mua ngay"],
    "ad_snapshot_url": "https://www.facebook.com/ads/archive/render?id=meta_ad_001",
    "ad_delivery_start_time": "2026-03-01T00:00:00+0000",
    "ad_delivery_stop_time": None,
    "impressions": {"lower_bound": "1000", "upper_bound": "5000"},
    "spend": {"lower_bound": "50", "upper_bound": "200"},
    "languages": ["vi"],
    "target_gender": "female",
    "target_locations": {"countries": ["VN", "TH"]},
    "publisher_platforms": ["facebook", "instagram"],
    "demographic_distribution": [
        {"age": "25-34", "gender": "female", "percentage": "0.45"}
    ],
    "bylines": "Paid for by Shop Thoi Trang VN",
}

SAMPLE_META_RAW_CAROUSEL = {
    "id": "meta_ad_002",
    "page_id": "987654321",
    "page_name": "Beauty Store",
    "ad_creative_bodies": ["Body 1", "Body 2"],
    "ad_creative_link_titles": ["Title 1", "Title 2"],
    "ad_creative_link_captions": [],
    "ad_snapshot_url": "https://www.facebook.com/ads/archive/render?id=meta_ad_002",
    "ad_delivery_start_time": "2026-02-15T00:00:00+0000",
    "ad_delivery_stop_time": "2026-03-15T00:00:00+0000",
    "impressions": {},
    "spend": {},
    "languages": [],
    "target_gender": "",
    "target_locations": [],
    "publisher_platforms": ["facebook"],
}

SAMPLE_TIKTOK_RAW = {
    "id": "tt_ad_001",
    "material_id": "tt_mat_001",
    "brand_name": "VN Beauty Official",
    "advertiser_id": "adv_789",
    "ad_title": "Serum Vitamin C",
    "ad_text": "Sang da chi sau 7 ngay",
    "video_info": {
        "cover": "https://p16.tiktokcdn.com/cover.jpg",
        "url": "https://v16.tiktokcdn.com/video.mp4",
        "duration": 15,
    },
    "landing_page_url": "https://shop.example.com/serum",
    "like": 5200,
    "comment": 340,
    "share": 120,
    "country_code": "VN",
    "industry_name": "Beauty & Personal Care",
    "tag": ["skincare", "serum", "vitamin c"],
    "cta": "Shop Now",
    "create_time": "2026-03-10T00:00:00Z",
}

SAMPLE_TIKTOK_RAW_MINIMAL = {
    "material_id": "tt_mat_002",
    "title": "Fallback title",
    "text": "Fallback text",
    "video_info": {},
    "like": None,
    "comment": 0,
    "share": None,
    "tag": "not_a_list",
}


# ---------------------------------------------------------------------------
# Meta Normalize Tests
# ---------------------------------------------------------------------------
class TestMetaNormalize:
    def setup_method(self):
        self.collector = MetaCollector()

    def test_normalize_full_response(self):
        result = self.collector.normalize(SAMPLE_META_RAW)

        assert result["platform"] == "meta"
        assert result["platform_ad_id"] == "meta_ad_001"
        assert result["advertiser_id"] == "123456789"
        assert result["advertiser_name"] == "Shop Thoi Trang VN"
        assert result["advertiser_page_url"] == "https://facebook.com/123456789"
        assert result["ad_type"] == "image"
        assert result["headline"] == "Flash Sale Mua He"
        assert result["body_text"] == "Giam gia 50% tat ca san pham"
        assert result["cta_type"] == "Mua ngay"
        assert result["impressions_lower"] == 1000
        assert result["impressions_upper"] == 5000
        assert result["spend_lower"] == 50.0
        assert result["spend_upper"] == 200.0
        assert result["target_countries"] == ["VN", "TH"]
        assert result["target_gender"] == "female"
        assert result["language"] == "vi"
        assert result["is_active"] is True
        assert result["first_seen"] == "2026-03-01T00:00:00+0000"
        assert result["thumbnail_url"] is not None
        assert len(result["media_urls"]) == 1

    def test_normalize_carousel_type(self):
        result = self.collector.normalize(SAMPLE_META_RAW_CAROUSEL)

        assert result["ad_type"] == "carousel"
        assert result["headline"] == "Title 1 | Title 2"
        assert result["body_text"] == "Body 1 | Body 2"
        assert result["cta_type"] is None

    def test_normalize_stopped_ad(self):
        result = self.collector.normalize(SAMPLE_META_RAW_CAROUSEL)

        assert result["is_active"] is False
        assert result["last_seen"] == "2026-03-15T00:00:00+0000"

    def test_normalize_missing_fields(self):
        result = self.collector.normalize({"id": "empty_ad"})

        assert result["platform"] == "meta"
        assert result["platform_ad_id"] == "empty_ad"
        assert result["headline"] is None
        assert result["body_text"] is None
        assert result["target_countries"] == ["VN"]
        assert result["language"] == "vi"
        assert result["impressions_lower"] is None
        assert result["spend_lower"] is None

    def test_detect_video_type(self):
        raw = {"ad_snapshot_url": "https://facebook.com/ads/video/123"}
        assert MetaCollector._detect_ad_type(raw) == "video"


# ---------------------------------------------------------------------------
# TikTok Normalize Tests
# ---------------------------------------------------------------------------
class TestTikTokNormalize:
    def setup_method(self):
        self.collector = TikTokCollector()

    def test_normalize_full_response(self):
        result = self.collector.normalize(SAMPLE_TIKTOK_RAW)

        assert result["platform"] == "tiktok"
        assert result["platform_ad_id"] == "tt_ad_001"
        assert result["advertiser_id"] == "adv_789"
        assert result["advertiser_name"] == "VN Beauty Official"
        assert result["ad_type"] == "video"
        assert result["headline"] == "Serum Vitamin C"
        assert result["body_text"] == "Sang da chi sau 7 ngay"
        assert result["thumbnail_url"] == "https://p16.tiktokcdn.com/cover.jpg"
        assert result["media_urls"] == ["https://v16.tiktokcdn.com/video.mp4"]
        assert result["landing_page_url"] == "https://shop.example.com/serum"
        assert result["likes"] == 5200
        assert result["comments"] == 340
        assert result["shares"] == 120
        assert result["target_countries"] == ["VN"]
        assert result["category"] == "Beauty & Personal Care"
        assert result["tags"] == ["skincare", "serum", "vitamin c"]
        assert result["cta_type"] == "Shop Now"
        assert result["is_active"] is True

    def test_normalize_minimal_response(self):
        result = self.collector.normalize(SAMPLE_TIKTOK_RAW_MINIMAL)

        assert result["platform_ad_id"] == "tt_mat_002"
        assert result["headline"] == "Fallback title"
        assert result["body_text"] == "Fallback text"
        assert result["thumbnail_url"] is None
        assert result["media_urls"] == []
        assert result["likes"] == 0
        assert result["comments"] == 0
        assert result["shares"] == 0
        assert result["tags"] == []  # non-list tag ignored

    def test_normalize_null_engagement(self):
        raw = {
            "material_id": "tt_003",
            "video_info": {},
            "like": None,
            "comment": None,
            "share": None,
        }
        result = self.collector.normalize(raw)
        assert result["likes"] == 0
        assert result["comments"] == 0
        assert result["shares"] == 0


# ---------------------------------------------------------------------------
# Meta Fetch with Mock httpx
# ---------------------------------------------------------------------------
class TestMetaFetch:
    @pytest.mark.asyncio
    async def test_fetch_single_page(self):
        collector = MetaCollector()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [SAMPLE_META_RAW],
            "paging": {},
        }

        with patch("app.collectors.meta_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await collector.collect({"search_terms": "test", "limit": 10, "max_pages": 1})

        assert len(result) == 1
        assert result[0]["id"] == "meta_ad_001"

    @pytest.mark.asyncio
    async def test_fetch_pagination(self):
        collector = MetaCollector()

        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.raise_for_status = MagicMock()
        page1_response.json.return_value = {
            "data": [SAMPLE_META_RAW],
            "paging": {"next": "https://graph.facebook.com/v19.0/ads_archive?after=cursor1"},
        }

        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.raise_for_status = MagicMock()
        page2_response.json.return_value = {
            "data": [SAMPLE_META_RAW_CAROUSEL],
            "paging": {},
        }

        with patch("app.collectors.meta_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[page1_response, page2_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await collector.collect({"search_terms": "test", "max_pages": 5})

        assert len(result) == 2
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_raises_on_429(self):
        collector = MetaCollector()

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("app.collectors.meta_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RateLimitError):
                await collector.collect({"search_terms": "test", "max_pages": 1})


# ---------------------------------------------------------------------------
# TikTok Fetch with Mock httpx
# ---------------------------------------------------------------------------
class TestTikTokFetch:
    @pytest.mark.asyncio
    async def test_fetch_single_page(self):
        collector = TikTokCollector()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {"materials": [SAMPLE_TIKTOK_RAW]},
        }

        with patch("app.collectors.tiktok_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await collector.collect({"limit": 10, "max_pages": 1})

        assert len(result) == 1
        assert result[0]["id"] == "tt_ad_001"

    @pytest.mark.asyncio
    async def test_fetch_stops_on_empty_page(self):
        collector = TikTokCollector()

        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.raise_for_status = MagicMock()
        page1_response.json.return_value = {
            "data": {"materials": [SAMPLE_TIKTOK_RAW]},
        }

        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.raise_for_status = MagicMock()
        page2_response.json.return_value = {
            "data": {"materials": []},
        }

        with patch("app.collectors.tiktok_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[page1_response, page2_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await collector.collect({"max_pages": 5})

        assert len(result) == 1
        assert mock_client.get.call_count == 2


# ---------------------------------------------------------------------------
# Upsert Logic Tests
# ---------------------------------------------------------------------------
class TestUpsertAds:
    @pytest.mark.asyncio
    async def test_insert_new_ads(self, db):
        collector = MetaCollector()
        ad1 = collector.normalize(SAMPLE_META_RAW)
        ad2 = collector.normalize(SAMPLE_META_RAW_CAROUSEL)

        result = await upsert_ads(db, [ad1, ad2])

        assert result["new"] == 2
        assert result["updated"] == 0
        assert len(result["ads"]) == 2
        # All ads should have an id assigned
        for ad in result["ads"]:
            assert "id" in ad

    @pytest.mark.asyncio
    async def test_update_existing_ad(self, db):
        collector = MetaCollector()
        ad_data = collector.normalize(SAMPLE_META_RAW)

        # Insert first time
        result1 = await upsert_ads(db, [ad_data])
        assert result1["new"] == 1

        # Update with new engagement
        ad_data_updated = collector.normalize(SAMPLE_META_RAW)
        ad_data_updated["likes"] = 500
        ad_data_updated["comments"] = 50

        result2 = await upsert_ads(db, [ad_data_updated])
        assert result2["new"] == 0
        assert result2["updated"] == 1

    @pytest.mark.asyncio
    async def test_mixed_insert_and_update(self, db):
        collector = MetaCollector()
        ad1 = collector.normalize(SAMPLE_META_RAW)

        # Insert ad1
        await upsert_ads(db, [ad1])

        # Now upsert ad1 (existing) + ad2 (new)
        ad2 = collector.normalize(SAMPLE_META_RAW_CAROUSEL)
        result = await upsert_ads(db, [ad1, ad2])

        assert result["new"] == 1
        assert result["updated"] == 1


# ---------------------------------------------------------------------------
# ES Indexing Tests
# ---------------------------------------------------------------------------
class TestIndexAdsToEs:
    @pytest.mark.asyncio
    async def test_index_ads(self, mock_es):
        ads = [
            {"id": "ad-1", "platform": "meta", "headline": "Test 1"},
            {"id": "ad-2", "platform": "tiktok", "headline": "Test 2"},
        ]

        count = await index_ads_to_es(mock_es, ads)

        assert count == 2
        mock_es.bulk.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_empty_list(self, mock_es):
        count = await index_ads_to_es(mock_es, [])

        assert count == 0
        mock_es.bulk.assert_not_called()


# ---------------------------------------------------------------------------
# Retry on 429 Tests
# ---------------------------------------------------------------------------
class TestRetryOn429:
    @pytest.mark.asyncio
    async def test_retry_and_succeed(self):
        collector = MetaCollector()

        # First call raises RateLimitError, second succeeds
        call_count = 0

        async def mock_collect(params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("429")
            return [SAMPLE_META_RAW]

        collector.collect = mock_collect

        with patch("app.collectors.base.asyncio.sleep", new_callable=AsyncMock):
            result = await collector.collect_with_retry({"search_terms": "test"}, max_retries=3)

        assert len(result) == 1
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        collector = MetaCollector()

        async def mock_collect(params):
            raise RateLimitError("429")

        collector.collect = mock_collect

        with patch("app.collectors.base.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RateLimitError):
                await collector.collect_with_retry({"search_terms": "test"}, max_retries=2)
