"""Tests for competitor alerts and notifications."""
import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers


@pytest.mark.asyncio
class TestAlertsCRUD:
    async def test_create_alert(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.post("/api/alerts", headers=headers, json={
            "name": "Shopee Ads",
            "alert_type": "advertiser_name",
            "match_value": "Shopee",
            "platforms": ["meta"],
        })
        # Free tier may or may not allow alerts — accept 201 or 403
        assert resp.status_code in (201, 403)
        if resp.status_code == 201:
            data = resp.json()
            assert data["name"] == "Shopee Ads"

    async def test_create_alert_unauthenticated(self, async_client: AsyncClient):
        resp = await async_client.post("/api/alerts", json={
            "name": "Test", "alert_type": "keyword", "match_value": "test",
        })
        assert resp.status_code in (401, 403)

    async def test_list_alerts(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.get("/api/alerts", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_crud_flow(self, async_client: AsyncClient, pro_user):
        """Full CRUD flow: create → list → toggle → delete."""
        headers = make_auth_headers(pro_user)

        # Create
        resp = await async_client.post("/api/alerts", headers=headers, json={
            "name": "Test CRUD",
            "alert_type": "keyword",
            "match_value": "test keyword",
            "platforms": ["meta", "tiktok"],
        })
        assert resp.status_code == 201
        alert_id = resp.json()["id"]

        # List — should contain the new alert
        resp = await async_client.get("/api/alerts", headers=headers)
        assert resp.status_code == 200
        names = [a["name"] for a in resp.json()]
        assert "Test CRUD" in names

        # Toggle — deactivate
        resp = await async_client.patch(
            f"/api/alerts/{alert_id}",
            headers=headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Delete
        resp = await async_client.delete(f"/api/alerts/{alert_id}", headers=headers)
        assert resp.status_code == 204


@pytest.mark.asyncio
class TestNotifications:
    async def test_list_notifications_empty(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.get("/api/notifications", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    async def test_unread_count(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.get(
            "/api/notifications/unread-count", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    async def test_mark_all_read(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.post(
            "/api/notifications/read-all", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
