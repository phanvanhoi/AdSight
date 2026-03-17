from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tier_limits import get_tier_limits
from app.models.user import User


async def check_search_limit(user: User, db: AsyncSession):
    """Check and increment daily search count. Raises 429 if limit exceeded."""
    limits = get_tier_limits(user.tier)
    if limits.searches_per_day == -1:
        return  # unlimited

    now = datetime.now(timezone.utc)

    # Reset daily count if new day
    if user.daily_search_reset is None or user.daily_search_reset.date() < now.date():
        user.daily_search_count = 0
        user.daily_search_reset = now

    if user.daily_search_count >= limits.searches_per_day:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "daily_search_limit",
                "message": f"Bạn đã hết {limits.searches_per_day} lượt tìm kiếm hôm nay. Nâng cấp Pro để unlimited.",
                "limit": limits.searches_per_day,
                "used": user.daily_search_count,
                "upgrade_url": "/pricing",
            },
        )

    user.daily_search_count += 1
    await db.commit()


async def check_ai_credits(user: User, db: AsyncSession):
    """Check AI credit availability. Raises 403/429 if exceeded."""
    limits = get_tier_limits(user.tier)
    if limits.ai_credits_per_month == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ai_not_available",
                "message": "AI Analysis chỉ có trong gói Pro trở lên.",
                "upgrade_url": "/pricing",
            },
        )

    now = datetime.now(timezone.utc)
    # Reset monthly
    credits_reset = user.ai_credits_reset
    if credits_reset and credits_reset.tzinfo is None:
        credits_reset = credits_reset.replace(tzinfo=timezone.utc)
    if credits_reset is None or (now - credits_reset) > timedelta(days=30):
        user.ai_credits_used = 0
        user.ai_credits_reset = now

    if user.ai_credits_used >= limits.ai_credits_per_month:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "ai_credits_exhausted",
                "message": f"Bạn đã dùng hết {limits.ai_credits_per_month} AI credits tháng này.",
                "limit": limits.ai_credits_per_month,
                "used": user.ai_credits_used,
            },
        )


async def consume_ai_credit(user: User, db: AsyncSession):
    """Consume 1 AI credit after successful analysis."""
    user.ai_credits_used += 1
    await db.commit()
