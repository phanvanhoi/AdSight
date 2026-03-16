"""Integration tests for /api/ads/search and /api/export endpoints."""
import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers


@pytest.mark.asyncio
class TestSearch:
    async def test_search_returns_schema(self, async_client: AsyncClient, mock_es):
        resp = await async_client.get("/api/ads/search", params={"q": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "results" in data
        assert "facets" in data
        assert isinstance(data["results"], list)
        facets = data["facets"]
        assert "platforms" in facets
        assert "ad_types" in facets
        assert "categories" in facets

    async def test_search_limit_over_100_422(self, async_client: AsyncClient):
        resp = await async_client.get(
            "/api/ads/search", params={"q": "test", "limit": 200}
        )
        assert resp.status_code == 422

    async def test_search_invalid_date_format_422(self, async_client: AsyncClient):
        resp = await async_client.get(
            "/api/ads/search", params={"q": "test", "date_from": "13-01-2025"}
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestExport:
    async def test_export_csv_has_bom(
        self, async_client: AsyncClient, test_user, mock_es
    ):
        headers = make_auth_headers(test_user)
        resp = await async_client.get("/api/export/csv", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        content = resp.text
        # UTF-8 BOM is \ufeff
        assert content.startswith("\ufeff")

    async def test_export_limit_by_tier(
        self, async_client: AsyncClient, test_user, pro_user, mock_es
    ):
        # Free tier → limit=100
        headers_free = make_auth_headers(test_user)
        resp = await async_client.get("/api/export/csv", headers=headers_free)
        assert resp.status_code == 200
        # Verify mock_es.search was called with size=100
        call_kwargs = mock_es.search.call_args
        assert call_kwargs.kwargs.get("size") == 100

        mock_es.search.reset_mock()

        # Pro tier → limit=5000
        headers_pro = make_auth_headers(pro_user)
        resp = await async_client.get("/api/export/csv", headers=headers_pro)
        assert resp.status_code == 200
        call_kwargs = mock_es.search.call_args
        assert call_kwargs.kwargs.get("size") == 5000
