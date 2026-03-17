from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import settings
from app.core.database import engine
from app.core.redis import redis_client
from app.search.es_client import es_client
from app.api.health import router as health_router
from app.api.router import api_router


async def _ensure_es_index():
    """Create ES index if it doesn't exist (auto-setup on first deploy)."""
    try:
        from app.search.indexing import ADS_INDEX_SETTINGS
        es = es_client.client
        index = settings.es_ads_index
        if not await es.indices.exists(index=index):
            await es.indices.create(
                index=index,
                settings=ADS_INDEX_SETTINGS["settings"],
                mappings=ADS_INDEX_SETTINGS["mappings"],
            )
    except Exception:
        pass  # Non-fatal — init_es script can still be used manually


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — Redis/ES are optional, app should still serve auth & API
    try:
        await redis_client.initialize()
    except Exception:
        pass  # Rate limiting degrades gracefully
    try:
        await es_client.initialize()
        await _ensure_es_index()
    except Exception:
        pass  # Search unavailable but auth/CRUD still work
    yield
    # Shutdown
    await engine.dispose()
    await redis_client.close()
    await es_client.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handle Pydantic ValidationError from manual model construction as 422
@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request, exc):
    errors = []
    for err in exc.errors():
        clean = {k: v for k, v in err.items() if k != "ctx"}
        errors.append(clean)
    return JSONResponse(status_code=422, content={"detail": errors})

# Routes
app.include_router(api_router, prefix="/api")
app.include_router(health_router, prefix="/api")
