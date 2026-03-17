"""Celery tasks for billing — check expired VNPay/MoMo subscriptions."""
import asyncio
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select

from app.core.database import async_session
from app.models.user import User


@shared_task(name="check_expired_subscriptions")
def check_expired_subscriptions():
    """Chạy hàng ngày — downgrade users có subscription hết hạn (VNPay/MoMo)."""
    asyncio.run(_check_expired())


async def _check_expired():
    async with async_session() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(User).where(
                User.subscription_end < now,
                User.subscription_status == "active",
                User.payment_method.in_(["vnpay", "momo"]),
            )
        )
        expired_users = result.scalars().all()

        for user in expired_users:
            user.tier = "free"
            user.subscription_status = "expired"

        if expired_users:
            await db.commit()
            print(f"Downgraded {len(expired_users)} expired VNPay/MoMo subscriptions")
