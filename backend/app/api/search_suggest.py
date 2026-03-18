"""Search suggestions / autocomplete API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.models.ad import Ad
from app.search.es_client import get_es

router = APIRouter()


@router.get("/search/suggest")
async def search_suggest(
    q: str = Query(min_length=2),
    limit: int = Query(default=5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    es=Depends(get_es),
):
    """Return autocomplete suggestions based on headline prefix match."""
    if es is None:
        return await _suggest_pg(q, limit, db)

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


async def _suggest_pg(q: str, limit: int, db: AsyncSession) -> dict:
    """Postgres fallback for autocomplete."""
    result = await db.execute(
        select(Ad.headline)
        .where(Ad.headline.ilike(f"%{q}%"))
        .limit(limit * 3)
    )
    seen: set[str] = set()
    suggestions: list[dict] = []
    for (headline,) in result.all():
        if not headline:
            continue
        short = headline[:50].strip()
        if short not in seen:
            seen.add(short)
            suggestions.append({"text": headline[:60], "score": 1.0})
        if len(suggestions) >= limit:
            break
    return {"suggestions": suggestions}
