"""Tests for Google Ads Transparency collector — 7 tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.collectors.google_collector import GoogleAdsCollector


class TestGoogleNormalize:
    def setup_method(self):
        self.collector = GoogleAdsCollector()

    def test_text_ad_search(self):
        raw = {
            "creative_id": "g_001",
            "advertiser_name": "Test VN Corp",
            "format": "TEXT",
            "headline": "Mua hàng online giá rẻ",
            "description": "Giảm 50% toàn bộ",
            "platforms": ["SEARCH"],
            "region": "VN",
            "first_shown": "2026-03-01T00:00:00Z",
        }
        result = self.collector.normalize(raw)
        assert result["platform"] == "google"
        assert result["platform_ad_id"] == "g_001"
        assert result["ad_type"] == "text"
        assert result["headline"] == "Mua hàng online giá rẻ"
        assert result["tags"] == ["SEARCH"]

    def test_image_ad_display(self):
        raw = {
            "creative_id": "g_002",
            "format": "DISPLAY",
            "advertiser": "Brand XYZ",
            "image_url": "https://img.example.com/banner.jpg",
            "destination_url": "https://brand.com",
        }
        result = self.collector.normalize(raw)
        assert result["ad_type"] == "image"
        assert result["media_urls"] == ["https://img.example.com/banner.jpg"]
        assert result["landing_page_url"] == "https://brand.com"

    def test_video_ad_youtube(self):
        raw = {
            "id": "g_003",
            "creative_type": "YOUTUBE",
            "title": "Product Demo",
            "video_thumbnail": "https://img.youtube.com/thumb.jpg",
        }
        result = self.collector.normalize(raw)
        assert result["ad_type"] == "video"
        assert result["thumbnail_url"] == "https://img.youtube.com/thumb.jpg"

    def test_missing_fields_defaults(self):
        raw = {"creative_id": "g_004"}
        result = self.collector.normalize(raw)
        assert result["platform_ad_id"] == "g_004"
        assert result["ad_type"] == "text"
        assert result["headline"] is None
        assert result["likes"] == 0
        assert result["is_active"] is True


class TestGoogleFetch:
    @pytest.mark.asyncio
    async def test_single_page(self):
        collector = GoogleAdsCollector()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "creatives": [
                {"creative_id": "1", "headline": "Ad 1"},
                {"creative_id": "2", "headline": "Ad 2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            ads = await collector.collect({"query": "test", "max_pages": 1})

        assert len(ads) == 2

    @pytest.mark.asyncio
    async def test_empty_response_stops(self):
        collector = GoogleAdsCollector()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"creatives": []}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            ads = await collector.collect({"query": "test", "max_pages": 3})

        assert len(ads) == 0

    @pytest.mark.asyncio
    async def test_non_200_stops(self):
        collector = GoogleAdsCollector()
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            ads = await collector.collect({"query": "test", "max_pages": 3})

        assert len(ads) == 0
