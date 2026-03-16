from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.ads import router as ads_router
from app.api.boards import router as boards_router
from app.api.dashboard import router as dashboard_router
from app.api.export import router as export_router
from app.api.tiktok_shop import router as tiktok_shop_router
from app.api.advertisers import router as advertisers_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(ads_router, prefix="/ads", tags=["Ads"])
api_router.include_router(boards_router, prefix="/boards", tags=["Boards"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])
api_router.include_router(tiktok_shop_router, prefix="/tiktok-shop", tags=["TikTok Shop"])
api_router.include_router(advertisers_router, prefix="/advertisers", tags=["Advertisers"])
