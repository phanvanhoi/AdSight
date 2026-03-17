"""Tests for user settings, telegram connect, daily digest preferences."""
import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers


@pytest.mark.asyncio
class TestUserSettings:
    async def test_get_me_has_all_fields(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # Phase 2 fields
        assert "email_alerts_enabled" in data
        assert "daily_digest_enabled" in data
        assert "telegram_connected" in data
        assert "telegram_enabled" in data
        assert "usage" in data
        assert "ai_credits" in data["usage"]

    async def test_update_email_alerts(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.patch(
            "/api/auth/settings",
            headers=headers,
            json={"email_alerts_enabled": False},
        )
        assert resp.status_code == 200

        # Verify
        me = await async_client.get("/api/auth/me", headers=headers)
        assert me.json()["email_alerts_enabled"] is False

    async def test_update_daily_digest(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.patch(
            "/api/auth/settings",
            headers=headers,
            json={"daily_digest_enabled": False},
        )
        assert resp.status_code == 200

        me = await async_client.get("/api/auth/me", headers=headers)
        assert me.json()["daily_digest_enabled"] is False

    async def test_update_telegram_enabled(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.patch(
            "/api/auth/settings",
            headers=headers,
            json={"telegram_enabled": True},
        )
        assert resp.status_code == 200

    async def test_update_full_name(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.patch(
            "/api/auth/settings",
            headers=headers,
            json={"full_name": "Updated Name"},
        )
        assert resp.status_code == 200
        me = await async_client.get("/api/auth/me", headers=headers)
        assert me.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
class TestTelegramConnect:
    async def test_connect_returns_url(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.post(
            "/api/auth/telegram/connect", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "connect_url" in data
        assert "token" in data
        assert "t.me/" in data["connect_url"]

    async def test_disconnect(
        self, async_client: AsyncClient, test_user, db
    ):
        test_user.telegram_chat_id = "123456"
        test_user.telegram_enabled = True
        await db.commit()

        headers = make_auth_headers(test_user)
        resp = await async_client.post(
            "/api/auth/telegram/disconnect", headers=headers
        )
        assert resp.status_code == 200

        me = await async_client.get("/api/auth/me", headers=headers)
        assert me.json()["telegram_connected"] is False
        assert me.json()["telegram_enabled"] is False
