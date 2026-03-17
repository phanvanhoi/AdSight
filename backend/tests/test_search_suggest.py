"""Tests for search autocomplete/suggestions."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSearchSuggest:
    async def test_suggest_returns_suggestions(
        self, async_client: AsyncClient, mock_es
    ):
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"headline": "Kem chống nắng SPF50"}, "_score": 5.0},
                    {"_source": {"headline": "Kem chống nắng cho da dầu"}, "_score": 4.5},
                    {"_source": {"headline": "Kem dưỡng da ban đêm"}, "_score": 3.0},
                ]
            }
        }
        resp = await async_client.get(
            "/api/search/suggest", params={"q": "kem", "limit": 5}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3
        assert data["suggestions"][0]["text"] == "Kem chống nắng SPF50"

    async def test_suggest_min_length(self, async_client: AsyncClient):
        """Query must be >= 2 chars."""
        resp = await async_client.get(
            "/api/search/suggest", params={"q": "k"}
        )
        assert resp.status_code == 422

    async def test_suggest_deduplication(
        self, async_client: AsyncClient, mock_es
    ):
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"headline": "Kem chống nắng"}, "_score": 5.0},
                    {"_source": {"headline": "Kem chống nắng"}, "_score": 4.0},
                    {"_source": {"headline": "Kem dưỡng"}, "_score": 3.0},
                ]
            }
        }
        resp = await async_client.get(
            "/api/search/suggest", params={"q": "kem"}
        )
        data = resp.json()
        assert len(data["suggestions"]) == 2

    async def test_suggest_empty_results(
        self, async_client: AsyncClient, mock_es
    ):
        mock_es.search.return_value = {"hits": {"hits": []}}
        resp = await async_client.get(
            "/api/search/suggest", params={"q": "xyznonexistent"}
        )
        assert resp.status_code == 200
        assert resp.json()["suggestions"] == []

    async def test_suggest_limit_param(
        self, async_client: AsyncClient, mock_es
    ):
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"headline": f"Ad {i}"}, "_score": float(5 - i)}
                    for i in range(10)
                ]
            }
        }
        resp = await async_client.get(
            "/api/search/suggest", params={"q": "ad", "limit": 3}
        )
        data = resp.json()
        assert len(data["suggestions"]) <= 3
