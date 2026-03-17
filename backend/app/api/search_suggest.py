"""Search suggestions / autocomplete API."""
from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.search.es_client import get_es

router = APIRouter()


@router.get("/search/suggest")
async def search_suggest(
    q: str = Query(min_length=2),
    limit: int = Query(default=5, ge=1, le=10),
    es=Depends(get_es),
):
    """Return autocomplete suggestions based on headline prefix match."""
    result = await es.search(
        index=settings.es_ads_index,
        body={
            "size": limit * 3,
            "query": {
                "match_phrase_prefix": {
                    "headline": {
                        "query": q,
                        "max_expansions": 20,
                    }
                }
            },
            "_source": ["headline"],
        },
    )

    seen: set[str] = set()
    suggestions: list[dict] = []
    for hit in result["hits"]["hits"]:
        headline = hit["_source"].get("headline", "")
        if not headline:
            continue
        short = headline[:50].strip()
        if short not in seen:
            seen.add(short)
            suggestions.append({"text": headline[:60], "score": hit["_score"]})
        if len(suggestions) >= limit:
            break

    return {"suggestions": suggestions}
