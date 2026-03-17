import uuid as _uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, String, TypeDecorator, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.models.base import Base
from app.models.user import User
from app.models.ad import Ad
from app.models.competitor_alert import CompetitorAlert
from app.models import *  # noqa: F401,F403 — ensure all models register with Base.metadata


# ---------------------------------------------------------------------------
# SQLite compatibility: UUID stored as CHAR(32), JSONB → JSON
# ---------------------------------------------------------------------------
class SQLiteUUID(TypeDecorator):
    """Store UUID as a 32-char hex string in SQLite."""
    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, _uuid.UUID):
                return value.hex
            return str(value).replace("-", "")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return _uuid.UUID(value)
        return value


for table in Base.metadata.tables.values():
    for column in table.columns:
        if isinstance(column.type, JSONB):
            column.type = JSON()
        elif isinstance(column.type, PG_UUID):
            column.type = SQLiteUUID()

# ---------------------------------------------------------------------------
# Database — in-memory SQLite async
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a DB session for tests."""
    async with TestSession() as session:
        yield session


# ---------------------------------------------------------------------------
# Mock external services
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_es():
    es = AsyncMock()
    es.search = AsyncMock(return_value={
        "hits": {"total": {"value": 0}, "hits": []},
        "aggregations": {
            "platforms": {"buckets": []},
            "ad_types": {"buckets": []},
            "categories": {"buckets": []},
            "categories_l1": {"buckets": []},
        },
    })
    es.count = AsyncMock(return_value={"count": 0})
    es.index = AsyncMock()
    es.bulk = AsyncMock()
    return es


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis


# ---------------------------------------------------------------------------
# FastAPI app with dependency overrides
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_client(mock_es, mock_redis):
    """httpx AsyncClient with all external deps mocked."""
    from app.core.database import get_db
    from app.core.redis import get_redis
    from app.main import app
    from app.search.es_client import get_es

    async def override_get_db():
        async with TestSession() as session:
            yield session

    async def override_get_es():
        return mock_es

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_es] = override_get_es
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------
TEST_PASSWORD = "testpass123"
TEST_EMAIL = "test@example.com"


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a free-tier test user."""
    user = User(
        email=TEST_EMAIL,
        hashed_password=hash_password(TEST_PASSWORD),
        full_name="Test User",
        is_active=True,
        tier="free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db: AsyncSession) -> User:
    """Create an inactive user."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password(TEST_PASSWORD),
        full_name="Inactive User",
        is_active=False,
        tier="free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def pro_user(db: AsyncSession) -> User:
    """Create a pro-tier user."""
    user = User(
        email="pro@example.com",
        hashed_password=hash_password(TEST_PASSWORD),
        full_name="Pro User",
        is_active=True,
        tier="pro",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def make_auth_headers(user: User) -> dict:
    """Generate Authorization headers for a user."""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    return make_auth_headers(test_user)


@pytest.fixture
def sample_ad_data():
    return {
        "platform": "meta",
        "platform_ad_id": "test_123",
        "advertiser_name": "Test Store",
        "ad_type": "image",
        "headline": "Test Ad",
        "body_text": "This is a test ad",
        "target_countries": ["VN"],
        "likes": 100,
        "comments": 10,
        "shares": 5,
        "is_active": True,
    }


@pytest_asyncio.fixture
async def agency_user(db: AsyncSession) -> User:
    """Create an agency-tier user."""
    user = User(
        email="agency@example.com",
        hashed_password=hash_password(TEST_PASSWORD),
        full_name="Agency User",
        is_active=True,
        tier="agency",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_ad(db: AsyncSession) -> Ad:
    """Create a sample ad in the database."""
    ad = Ad(
        platform="meta",
        platform_ad_id="test_ad_001",
        advertiser_name="Test Store",
        ad_type="image",
        headline="Kem chống nắng SPF50 giảm 30%",
        body_text="Sản phẩm bán chạy nhất mùa hè",
        target_countries=["VN"],
        likes=500,
        comments=20,
        shares=10,
        is_active=True,
        category_l1="Mỹ phẩm",
        category_l2="Kem chống nắng",
        viral_score=65.0,
        engagement_rate=3.2,
        estimated_daily_spend=50.0,
        estimated_total_spend=1500.0,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


@pytest_asyncio.fixture
async def sample_alert(db: AsyncSession, test_user: User) -> CompetitorAlert:
    """Create a sample competitor alert."""
    alert = CompetitorAlert(
        user_id=test_user.id,
        name="Test Alert",
        alert_type="advertiser_name",
        match_value="Shopee",
        platforms=["meta", "tiktok"],
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert
