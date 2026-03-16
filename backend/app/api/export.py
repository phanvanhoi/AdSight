from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest
from app.search.es_client import get_es
from app.services.export_service import export_ads_csv

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
    es=Depends(get_es),
):
    request = SearchRequest(
        q=q, platform=platform, country=country, ad_type=ad_type,
        date_from=date_from, date_to=date_to, min_likes=min_likes,
        sort=sort, page=1, limit=100 if user.tier == "free" else 1000,
    )
    csv_content = await export_ads_csv(es, request)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ads_export.csv"},
    )
