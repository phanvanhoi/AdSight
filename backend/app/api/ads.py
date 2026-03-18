from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.usage import check_ai_credits, check_search_limit, consume_ai_credit
from app.dependencies import get_current_user, get_optional_user
from app.models.ad import Ad
from app.models.user import User
from app.schemas.ad import AdDetailResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.search.es_client import get_es
from app.services.ai_analysis import analyze_ad_creative
from app.services.search_service import search_ads
from app.services.search_service_pg import search_ads_pg

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
    category_l1: str | None = Query(default=None, description="Category L1 filter"),
    min_spend: float | None = Query(default=None, ge=0, description="Min daily spend"),
    max_spend: float | None = Query(default=None, ge=0, description="Max daily spend"),
    min_viral_score: float | None = Query(default=None, ge=0, description="Min viral score"),
    is_hot: bool | None = Query(default=None, description="Only hot ads"),
    has_discount: bool | None = Query(default=None, description="Only ads with discount"),
    sort: str = Query(default="relevance", description="Sort: relevance,newest,engagement,viral"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    es=Depends(get_es),
):
    # Check search limit for authenticated users
    if user:
        await check_search_limit(user, db)

    request = SearchRequest(
        q=q,
        platform=platform,
        country=country,
        ad_type=ad_type,
        date_from=date_from,
        date_to=date_to,
        min_likes=min_likes,
        category_l1=category_l1,
        min_spend=min_spend,
        max_spend=max_spend,
        min_viral_score=min_viral_score,
        is_hot=is_hot,
        has_discount=has_discount,
        sort=sort,
        page=page,
        limit=limit,
    )
    if es is None:
        return await search_ads_pg(db, request)
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


@router.post("/{ad_id}/ai-analysis")
async def ai_analyze_ad(
    ad_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Phân tích ad bằng AI. Tốn 1 AI credit."""
    # Check credits
    await check_ai_credits(user, db)

    # Get ad
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Return cached analysis if exists (< 7 days old)
    if ad.ai_analysis and ad.ai_analyzed_at:
        analyzed_at = ad.ai_analyzed_at.replace(tzinfo=timezone.utc) if ad.ai_analyzed_at.tzinfo is None else ad.ai_analyzed_at
        age = (datetime.now(timezone.utc) - analyzed_at).days
        if age < 7:
            return {"analysis": ad.ai_analysis, "cached": True}

    # Run analysis
    try:
        analysis = await analyze_ad_creative(ad)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    # Save to DB
    ad.ai_analysis = analysis
    ad.ai_analyzed_at = datetime.now(timezone.utc)

    # Consume credit
    await consume_ai_credit(user, db)
    await db.commit()

    return {"analysis": analysis, "cached": False}
