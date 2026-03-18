from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.search import ExportSearchRequest
from app.search.es_client import get_es
from app.services.export_service import export_ads_csv, export_ads_csv_pg

router = APIRouter()


@router.get("/csv")
async def export_csv(
    q: str = Query(default=""),
    platform: str | None = None,
    country: str | None = None,
    ad_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_likes: int | None = None,
    sort: str = "newest",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    es=Depends(get_es),
):
    tier_limits = {"free": 100, "pro": 5000, "enterprise": 50000}
    export_limit = tier_limits.get(user.tier, 100)
    request = ExportSearchRequest(
        q=q, platform=platform, country=country, ad_type=ad_type,
        date_from=date_from, date_to=date_to, min_likes=min_likes,
        sort=sort, page=1, limit=export_limit,
    )
    if es is None:
        csv_content = await export_ads_csv_pg(db, request)
    else:
        csv_content = await export_ads_csv(es, request)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ads_export.csv"},
    )
