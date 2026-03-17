"""Integration tests for /api/boards endpoints."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.board import Board
from tests.conftest import make_auth_headers, TEST_PASSWORD


@pytest.mark.asyncio
class TestListBoards:
    async def test_list_boards_empty(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.get("/api/boards", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
class TestCreateBoard:
    async def test_create_board_success(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.post("/api/boards", json={
            "name": "My Board",
            "description": "Test board",
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Board"

    async def test_create_4th_board_free_tier_403(
        self, async_client: AsyncClient, test_user
    ):
        headers = make_auth_headers(test_user)
        # Create 3 boards (allowed for free tier)
        for i in range(3):
            resp = await async_client.post("/api/boards", json={
                "name": f"Board {i}",
            }, headers=headers)
            assert resp.status_code == 201

        # 4th should fail
        resp = await async_client.post("/api/boards", json={
            "name": "Board 4",
        }, headers=headers)
        assert resp.status_code == 403
        assert "3 boards" in resp.json()["detail"]


@pytest.mark.asyncio
class TestDeleteBoard:
    async def test_delete_own_board(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        create_resp = await async_client.post("/api/boards", json={
            "name": "To Delete",
        }, headers=headers)
        board_id = create_resp.json()["id"]

        resp = await async_client.delete(f"/api/boards/{board_id}", headers=headers)
        assert resp.status_code == 204

    async def test_delete_other_users_board_404(
        self, async_client: AsyncClient, test_user, pro_user
    ):
        # test_user creates a board
        headers_owner = make_auth_headers(test_user)
        create_resp = await async_client.post("/api/boards", json={
            "name": "Owner's Board",
        }, headers=headers_owner)
        board_id = create_resp.json()["id"]

        # pro_user tries to delete it
        headers_other = make_auth_headers(pro_user)
        resp = await async_client.delete(
            f"/api/boards/{board_id}", headers=headers_other
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestBoardAds:
    async def _create_ad(self, db: AsyncSession) -> Ad:
        ad = Ad(
            platform="meta",
            platform_ad_id=f"ad_{uuid.uuid4().hex[:8]}",
            advertiser_name="Test",
            ad_type="image",
        )
        db.add(ad)
        await db.commit()
        await db.refresh(ad)
        return ad

    async def test_add_and_remove_ad(
        self, async_client: AsyncClient, test_user, db: AsyncSession
    ):
        headers = make_auth_headers(test_user)
        ad = await self._create_ad(db)

        # Create board
        board_resp = await async_client.post("/api/boards", json={
            "name": "Ad Board",
        }, headers=headers)
        board_id = board_resp.json()["id"]

        # Add ad
        resp = await async_client.post(
            f"/api/boards/{board_id}/ads/{ad.id}", headers=headers
        )
        assert resp.status_code == 201

        # Remove ad
        resp = await async_client.delete(
            f"/api/boards/{board_id}/ads/{ad.id}", headers=headers
        )
        assert resp.status_code == 204

    async def test_add_51st_ad_free_tier_403(
        self, async_client: AsyncClient, test_user, db: AsyncSession
    ):
        headers = make_auth_headers(test_user)

        # Create board
        board_resp = await async_client.post("/api/boards", json={
            "name": "Full Board",
        }, headers=headers)
        board_id = board_resp.json()["id"]

        # Add 50 ads
        for i in range(50):
            ad = await self._create_ad(db)
            resp = await async_client.post(
                f"/api/boards/{board_id}/ads/{ad.id}", headers=headers
            )
            assert resp.status_code == 201, f"Failed on ad {i}: {resp.json()}"

        # 51st should fail
        ad51 = await self._create_ad(db)
        resp = await async_client.post(
            f"/api/boards/{board_id}/ads/{ad51.id}", headers=headers
        )
        assert resp.status_code == 403
        assert "50 ads" in resp.json()["detail"]


@pytest.mark.asyncio
class TestGetBoardAds:
    async def _create_ad(self, db: AsyncSession) -> Ad:
        ad = Ad(
            platform="meta",
            platform_ad_id=f"ad_{uuid.uuid4().hex[:8]}",
            advertiser_name="Test",
            ad_type="image",
        )
        db.add(ad)
        await db.commit()
        await db.refresh(ad)
        return ad

    async def test_get_board_ads_returns_paginated(
        self, async_client: AsyncClient, test_user, db: AsyncSession
    ):
        headers = make_auth_headers(test_user)

        # Create board + add 3 ads
        board_resp = await async_client.post("/api/boards", json={
            "name": "Ads Board",
        }, headers=headers)
        board_id = board_resp.json()["id"]

        for _ in range(3):
            ad = await self._create_ad(db)
            await async_client.post(
                f"/api/boards/{board_id}/ads/{ad.id}", headers=headers
            )

        resp = await async_client.get(
            f"/api/boards/{board_id}/ads", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert len(data["results"]) == 3

    async def test_get_board_ads_other_user_404(
        self, async_client: AsyncClient, test_user, pro_user
    ):
        headers_owner = make_auth_headers(test_user)
        board_resp = await async_client.post("/api/boards", json={
            "name": "Private Board",
        }, headers=headers_owner)
        board_id = board_resp.json()["id"]

        headers_other = make_auth_headers(pro_user)
        resp = await async_client.get(
            f"/api/boards/{board_id}/ads", headers=headers_other
        )
        assert resp.status_code == 404
