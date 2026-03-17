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


@pytest.mark.asyncio
class TestAdvancedFilters:
    async def test_search_with_category_filter(
        self, async_client: AsyncClient, mock_es
    ):
        resp = await async_client.get(
            "/api/ads/search",
            params={"q": "kem", "category_l1": "Mỹ phẩm"},
        )
        assert resp.status_code == 200
        # Verify ES was called with category filter in query kwarg
        call_kwargs = mock_es.search.call_args
        query = call_kwargs.kwargs.get("query", {})
        filters = query.get("bool", {}).get("filter", [])
        cat_filter = [f for f in filters if "term" in f and "category_l1" in f.get("term", {})]
        assert len(cat_filter) == 1

    async def test_search_with_spend_range(
        self, async_client: AsyncClient, mock_es
    ):
        resp = await async_client.get(
            "/api/ads/search",
            params={"q": "", "min_spend": 10, "max_spend": 100},
        )
        assert resp.status_code == 200

    async def test_search_with_is_hot(
        self, async_client: AsyncClient, mock_es
    ):
        resp = await async_client.get(
            "/api/ads/search",
            params={"q": "", "is_hot": True},
        )
        assert resp.status_code == 200

    async def test_search_sort_viral(
        self, async_client: AsyncClient, mock_es
    ):
        resp = await async_client.get(
            "/api/ads/search",
            params={"q": "", "sort": "viral"},
        )
        assert resp.status_code == 200
        call_kwargs = mock_es.search.call_args
        sort = call_kwargs.kwargs.get("sort", [])
        assert sort[0] == {"viral_score": {"order": "desc", "missing": "_last"}}
