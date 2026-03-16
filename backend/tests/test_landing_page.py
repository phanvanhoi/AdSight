"""Tests for landing page crawler — 14 tests."""

import pytest

from app.enrichment.landing_page import (
    detect_chat_widget,
    detect_pixels,
    detect_platform,
    extract_price,
    extract_product_image,
    extract_product_name,
)


# --- Platform detection (4 tests) ---
class TestDetectPlatform:
    def test_shopee_url(self):
        assert detect_platform("https://shopee.vn/product/123", "") == "shopee"

    def test_lazada_url(self):
        assert detect_platform("https://lazada.vn/item/456", "") == "lazada"

    def test_haravan_source(self):
        source = '<link rel="stylesheet" href="https://theme.myharavan.com/css/main.css">'
        assert detect_platform("https://example.com", source) == "haravan"

    def test_unknown_url(self):
        assert detect_platform("https://mysite.com", "<html></html>") == "custom"


# --- Pixel detection (3 tests) ---
class TestDetectPixels:
    def test_fb_pixel(self):
        source = '<script>fbq("track", "PageView")</script>'
        result = detect_pixels(source)
        assert result["fb_pixel"] is True
        assert result["tiktok_pixel"] is False

    def test_tiktok_pixel(self):
        source = '<script>ttq.track("ViewContent")</script>'
        result = detect_pixels(source)
        assert result["tiktok_pixel"] is True

    def test_google_analytics(self):
        source = '<script>gtag("config", "G-XXXXX")</script>'
        result = detect_pixels(source)
        assert result["google_analytics"] is True


# --- Chat widget (1 test) ---
class TestDetectChatWidget:
    def test_zalo_chat(self):
        source = '<div class="zalo-chat-widget" data-oaid="123"></div>'
        assert detect_chat_widget(source) == "zalo"

    def test_no_chat(self):
        assert detect_chat_widget("<html></html>") is None


# --- Price extraction (3 tests) ---
class TestExtractPrice:
    def test_vnd_dot_format(self):
        source = '<span class="price">199.000₫</span>'
        assert extract_price(source) == 199000.0

    def test_k_format(self):
        source = '<span>Chỉ 199K</span>'
        assert extract_price(source) == 199000.0

    def test_comma_format(self):
        source = '<span>Giá: 2,500,000 VND</span>'
        assert extract_price(source) == 2500000.0


# --- Product name extraction (1 test) ---
class TestExtractProductName:
    def test_og_title(self):
        source = '<meta property="og:title" content="Kem chống nắng SPF50">'
        assert extract_product_name(source) == "Kem chống nắng SPF50"

    def test_title_tag(self):
        source = "<title>Best Product Ever</title>"
        assert extract_product_name(source) == "Best Product Ever"


# --- Product image extraction (1 test) ---
class TestExtractProductImage:
    def test_og_image(self):
        source = '<meta property="og:image" content="https://img.example.com/product.jpg">'
        assert extract_product_image(source) == "https://img.example.com/product.jpg"

    def test_no_image(self):
        assert extract_product_image("<html></html>") is None
