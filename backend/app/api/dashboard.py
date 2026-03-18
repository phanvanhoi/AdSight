from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_optional_user
from app.models.user import User
from app.search.es_client import get_es
from app.services.dashboard_service import get_dashboard_overview, get_trending_ads
from app.services.dashboard_service_pg import get_dashboard_overview_pg, get_trending_ads_pg

router = APIRouter()


@router.get("/overview")
async def overview(
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    es=Depends(get_es),
):
    if es is None:
        return await get_dashboard_overview_pg(db)
    return await get_dashboard_overview(es)


@router.get("/trending")
async def trending(
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    es=Depends(get_es),
):
    if es is None:
        return await get_trending_ads_pg(db)
    return await get_trending_ads(es)
