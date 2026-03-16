from fastapi import APIRouter, Depends

from app.dependencies import get_optional_user
from app.models.user import User
from app.search.es_client import get_es
from app.services.dashboard_service import get_dashboard_overview, get_trending_ads

router = APIRouter()


@router.get("/overview")
async def overview(
    user: User | None = Depends(get_optional_user),
    es=Depends(get_es),
):
    return await get_dashboard_overview(es)


@router.get("/trending")
async def trending(
    user: User | None = Depends(get_optional_user),
    es=Depends(get_es),
):
    return await get_trending_ads(es)
