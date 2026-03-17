"""Tests for Telegram bot utilities."""
import pytest
from unittest.mock import AsyncMock, patch

from app.core.telegram import send_telegram_message, build_alert_message


class TestBuildAlertMessage:
    def test_basic_message(self):
        msg = build_alert_message(
            alert_name="Shopee Ads",
            match_value="Shopee",
            ad_count=3,
            ads_preview=[
                {"headline": "Test Ad 1", "platform": "meta"},
                {"headline": "Test Ad 2", "platform": "tiktok"},
            ],
        )
        assert "Shopee Ads" in msg
        assert "3" in msg
        assert "META" in msg
        assert "TIKTOK" in msg

    def test_message_with_overflow(self):
        msg = build_alert_message(
            alert_name="Alert",
            match_value="test",
            ad_count=10,
            ads_preview=[{"headline": f"Ad {i}", "platform": "meta"} for i in range(10)],
        )
        assert "5 ads khác" in msg

    def test_empty_preview(self):
        msg = build_alert_message("Alert", "test", 0, [])
        assert "Alert" in msg


@pytest.mark.asyncio
class TestSendTelegramMessage:
    @patch("app.core.telegram.settings")
    async def test_skip_if_no_token(self, mock_settings):
        mock_settings.telegram_bot_token = ""
        result = await send_telegram_message("123", "hello")
        assert result is False

    @patch("app.core.telegram.httpx.AsyncClient")
    @patch("app.core.telegram.settings")
    async def test_send_success(self, mock_settings, mock_client_cls):
        mock_settings.telegram_bot_token = "test-token"
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_resp
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_instance

        result = await send_telegram_message("123", "hello")
        assert result is True
