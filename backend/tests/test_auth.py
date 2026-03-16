"""Integration tests for /api/auth endpoints."""
import pytest
from httpx import AsyncClient

from tests.conftest import TEST_EMAIL, TEST_PASSWORD, make_auth_headers


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, async_client: AsyncClient):
        resp = await async_client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "securepass8",
            "full_name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["tier"] == "free"
        assert "id" in data

    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user):
        resp = await async_client.post("/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": "securepass8",
            "full_name": "Dup User",
        })
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_short_password(self, async_client: AsyncClient):
        resp = await async_client.post("/api/auth/register", json={
            "email": "short@example.com",
            "password": "abc",
            "full_name": "Short Pw",
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, async_client: AsyncClient, test_user):
        resp = await async_client.post("/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, async_client: AsyncClient, test_user):
        resp = await async_client.post("/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid email or password"

    async def test_login_inactive_user(self, async_client: AsyncClient, inactive_user):
        resp = await async_client.post("/api/auth/login", json={
            "email": "inactive@example.com",
            "password": TEST_PASSWORD,
        })
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"]


@pytest.mark.asyncio
class TestRefreshToken:
    async def test_refresh_success_blacklists_old(
        self, async_client: AsyncClient, test_user, mock_redis
    ):
        # Login to get tokens
        login_resp = await async_client.post("/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        })
        refresh_tok = login_resp.json()["refresh_token"]

        # Refresh
        resp = await async_client.post(
            "/api/auth/refresh", params={"refresh_token": refresh_tok}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # Verify old token was blacklisted via redis.setex
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "token_blacklist:" in call_args[0][0]


@pytest.mark.asyncio
class TestRateLimit:
    async def test_rate_limit_429(self, async_client: AsyncClient, mock_redis):
        _counter = {"val": 0}
        _expire_calls = []

        async def _incr_counter(key):
            _counter["val"] += 1
            return _counter["val"]

        async def _expire_spy(key, ttl):
            _expire_calls.append((key, ttl))

        mock_redis.incr = _incr_counter
        mock_redis.expire = _expire_spy

        last_status = None
        for i in range(12):
            resp = await async_client.post("/api/auth/login", json={
                "email": "nobody@example.com",
                "password": "doesntmatter",
            })
            last_status = resp.status_code
            if last_status == 429:
                break

        assert last_status == 429
        # Verify expire was called on the first incr (count == 1)
        assert len(_expire_calls) == 1
        assert _expire_calls[0][0].startswith("auth_rate:")
        assert _expire_calls[0][1] == 300


@pytest.mark.asyncio
class TestLogout:
    async def test_logout_success(self, async_client: AsyncClient, test_user):
        headers = make_auth_headers(test_user)
        resp = await async_client.post("/api/auth/logout", headers=headers)
        assert resp.status_code == 204

    async def test_logout_unauthenticated(self, async_client: AsyncClient):
        resp = await async_client.post("/api/auth/logout")
        assert resp.status_code in (401, 403)
