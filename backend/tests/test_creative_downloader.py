"""Tests for creative downloader — 8 tests."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enrichment.creative_downloader import analyze_image, MAX_IMAGE_SIZE


def _make_test_image(width=100, height=100, color=(255, 0, 0), fmt="JPEG") -> bytes:
    """Create a simple test image in memory."""
    from PIL import Image
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class TestAnalyzeImage:
    def test_valid_jpeg(self):
        img_bytes = _make_test_image(200, 150, (128, 64, 32), "JPEG")
        result = analyze_image(img_bytes)
        assert result["width"] == 200
        assert result["height"] == 150
        assert result["format"] == "jpeg"
        assert isinstance(result["phash"], str)
        assert len(result["phash"]) > 0
        assert isinstance(result["dominant_colors"], list)
        assert len(result["dominant_colors"]) <= 3

    def test_png_with_high_contrast(self):
        """Image with lots of black and white pixels → has_text_overlay likely True."""
        from PIL import Image
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        # Draw black text-like region (30% of pixels)
        for x in range(30):
            for y in range(100):
                img.putpixel((x, y), (0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = analyze_image(buf.getvalue())
        assert result["has_text_overlay"] is True

    def test_phash_similar_images(self):
        """Two similar images should have similar perceptual hashes."""
        import imagehash
        img1 = _make_test_image(100, 100, (255, 0, 0))
        img2 = _make_test_image(100, 100, (250, 5, 5))  # very similar
        h1 = analyze_image(img1)["phash"]
        h2 = analyze_image(img2)["phash"]
        # Convert hex strings to imagehash objects for distance comparison
        hash1 = imagehash.hex_to_hash(h1)
        hash2 = imagehash.hex_to_hash(h2)
        assert hash1 - hash2 < 10  # Hamming distance < 10

    def test_phash_different_images(self):
        """Two very different images should have different hashes."""
        import imagehash
        img1 = _make_test_image(100, 100, (255, 0, 0))  # solid red
        # Create a complex pattern image
        from PIL import Image
        img = Image.new("RGB", (100, 100))
        for x in range(100):
            for y in range(100):
                img.putpixel((x, y), ((x * 7) % 256, (y * 13) % 256, ((x + y) * 3) % 256))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img2_bytes = buf.getvalue()

        h1 = analyze_image(img1)["phash"]
        h2 = analyze_image(img2_bytes)["phash"]
        hash1 = imagehash.hex_to_hash(h1)
        hash2 = imagehash.hex_to_hash(h2)
        assert hash1 - hash2 > 10  # Different images


class TestDownloadAndAnalyze:
    @pytest.mark.asyncio
    async def test_mock_download_success(self):
        """Mock httpx download returns metadata."""
        import sys
        # Mock storage module to avoid boto3 dependency
        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock()
        sys.modules["app.core.storage"] = mock_storage

        from app.enrichment.creative_downloader import download_and_analyze_creative

        img_bytes = _make_test_image(300, 200)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.content = img_bytes

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_ad = MagicMock()
        mock_ad.thumbnail_url = "https://example.com/img.jpg"
        mock_ad.media_urls = []
        mock_ad.platform = "meta"
        mock_ad.platform_ad_id = "test_123"

        result = await download_and_analyze_creative(mock_ad, mock_client)

        assert result is not None
        assert result["creative_s3_key"].startswith("creatives/")
        assert result["creative_width"] == 300
        assert result["creative_height"] == 200

        del sys.modules["app.core.storage"]

    @pytest.mark.asyncio
    async def test_404_returns_none(self):
        """404 response returns None."""
        import sys
        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock()
        sys.modules["app.core.storage"] = mock_storage

        from app.enrichment.creative_downloader import download_and_analyze_creative

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_ad = MagicMock()
        mock_ad.thumbnail_url = "https://example.com/missing.jpg"
        mock_ad.media_urls = []

        result = await download_and_analyze_creative(mock_ad, mock_client)
        assert result is None

        del sys.modules["app.core.storage"]

    @pytest.mark.asyncio
    async def test_oversized_skipped(self):
        """Oversized image is skipped."""
        import sys
        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock()
        sys.modules["app.core.storage"] = mock_storage

        from app.enrichment.creative_downloader import download_and_analyze_creative

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.content = b"x" * (MAX_IMAGE_SIZE + 1)  # Too big

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_ad = MagicMock()
        mock_ad.thumbnail_url = "https://example.com/huge.jpg"
        mock_ad.media_urls = []

        result = await download_and_analyze_creative(mock_ad, mock_client)
        assert result is None

        del sys.modules["app.core.storage"]

    @pytest.mark.asyncio
    async def test_no_urls_returns_none(self):
        """Ad with no URLs returns None."""
        import sys
        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock()
        sys.modules["app.core.storage"] = mock_storage

        from app.enrichment.creative_downloader import download_and_analyze_creative

        mock_ad = MagicMock()
        mock_ad.thumbnail_url = None
        mock_ad.media_urls = None

        result = await download_and_analyze_creative(mock_ad, AsyncMock())
        assert result is None

        del sys.modules["app.core.storage"]
