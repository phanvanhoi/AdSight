from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_optional_user
from app.models.ad import Ad
from app.models.user import User
from app.schemas.ad import AdDetailResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.search.es_client import get_es
from app.services.search_service import search_ads

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(default="", description="Search query"),
    platform: str | None = Query(default=None, description="Platform filter: meta,tiktok"),
    country: str | None = Query(default=None, description="Country code: VN,TH,ID"),
    ad_type: str | None = Query(default=None, description="Ad type: image,video,carousel"),
    date_from: str | None = Query(default=None, description="Start date YYYY-MM-DD"),
    date_to: str | None = Query(default=None, description="End date YYYY-MM-DD"),
    min_likes: int | None = Query(default=None, ge=0),
    sort: str = Query(default="relevance", description="Sort: relevance,newest,engagement"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User | None = Depends(get_optional_user),
    es=Depends(get_es),
):
    request = SearchRequest(
        q=q,
        platform=platform,
        country=country,
        ad_type=ad_type,
        date_from=date_from,
        date_to=date_to,
        min_likes=min_likes,
        sort=sort,
        page=page,
        limit=limit,
    )
    return await search_ads(es, request)


@router.get("/{ad_id}", response_model=AdDetailResponse)
async def get_ad_detail(
    ad_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")
    return ad
