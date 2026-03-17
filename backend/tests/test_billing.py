"""Tests for billing / tier limits / usage tracking."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.tier_limits import get_tier_limits, TIER_LIMITS


# ---------------------------------------------------------------------------
# Tier limits config
# ---------------------------------------------------------------------------

def test_tier_limits_free():
    limits = get_tier_limits("free")
    assert limits.searches_per_day == 50
    assert limits.platforms == ["meta"]
    assert limits.max_boards == 3
    assert limits.max_saved_ads == 50
    assert limits.ai_credits_per_month == 0
    assert limits.can_export is True
    assert limits.export_max_rows == 100


def test_tier_limits_pro():
    limits = get_tier_limits("pro")
    assert limits.searches_per_day == -1  # unlimited
    assert "tiktok" in limits.platforms
    assert limits.max_boards == -1
    assert limits.ai_credits_per_month == 50


def test_tier_limits_agency():
    limits = get_tier_limits("agency")
    assert limits.searches_per_day == -1
    assert limits.ai_credits_per_month == 500
    assert limits.data_retention_days == -1


def test_tier_limits_unknown_falls_back_to_free():
    limits = get_tier_limits("unknown_tier")
    assert limits.searches_per_day == 50
    assert limits.platforms == ["meta"]


# ---------------------------------------------------------------------------
# Usage tracking
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_limit_free_user():
    """Free user hitting search limit should get 429."""
    from app.core.usage import check_search_limit
    from fastapi import HTTPException

    user = MagicMock()
    user.tier = "free"
    user.daily_search_count = 50
    user.daily_search_reset = datetime.now(timezone.utc)

    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await check_search_limit(user, db)
    assert exc_info.value.status_code == 429
    assert "daily_search_limit" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_search_limit_increments():
    """Search should increment daily count."""
    from app.core.usage import check_search_limit

    user = MagicMock()
    user.tier = "free"
    user.daily_search_count = 10
    user.daily_search_reset = datetime.now(timezone.utc)

    db = AsyncMock()

    await check_search_limit(user, db)
    assert user.daily_search_count == 11
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_unlimited_pro():
    """Pro user should not be limited."""
    from app.core.usage import check_search_limit

    user = MagicMock()
    user.tier = "pro"
    user.daily_search_count = 99999

    db = AsyncMock()

    # Should not raise
    await check_search_limit(user, db)
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_daily_search_reset():
    """Search count should reset on a new day."""
    from app.core.usage import check_search_limit

    user = MagicMock()
    user.tier = "free"
    user.daily_search_count = 50
    user.daily_search_reset = datetime.now(timezone.utc) - timedelta(days=1)

    db = AsyncMock()

    # Should reset count and allow search
    await check_search_limit(user, db)
    assert user.daily_search_count == 1  # reset to 0 then incremented


@pytest.mark.asyncio
async def test_ai_credits_free_user():
    """Free user should get 403 for AI features."""
    from app.core.usage import check_ai_credits
    from fastapi import HTTPException

    user = MagicMock()
    user.tier = "free"

    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await check_ai_credits(user, db)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_ai_credits_exhausted():
    """Pro user with exhausted credits should get 429."""
    from app.core.usage import check_ai_credits
    from fastapi import HTTPException

    user = MagicMock()
    user.tier = "pro"
    user.ai_credits_used = 50
    user.ai_credits_reset = datetime.now(timezone.utc)

    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await check_ai_credits(user, db)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_consume_ai_credit():
    """Consuming a credit should increment counter."""
    from app.core.usage import consume_ai_credit

    user = MagicMock()
    user.ai_credits_used = 5

    db = AsyncMock()

    await consume_ai_credit(user, db)
    assert user.ai_credits_used == 6
    db.commit.assert_awaited_once()
