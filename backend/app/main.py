from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import settings
from app.core.database import engine
from app.core.redis import redis_client
from app.search.es_client import es_client
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.initialize()
    await es_client.initialize()
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


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }
