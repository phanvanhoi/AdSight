"""Celery task — send Telegram alerts."""
import asyncio

from celery import shared_task
from sqlalchemy import select

from app.core.database import async_session
from app.core.telegram import build_alert_message, send_telegram_message
from app.models.ad import Ad
from app.models.user import User


@shared_task(name="send_telegram_alert")
def send_telegram_alert(user_id: str, alert_name: str, match_value: str, ad_count: int, ad_ids: list[str]):
    """Send Telegram alert to user."""
    asyncio.run(_send_telegram_alert(user_id, alert_name, match_value, ad_count, ad_ids))


async def _send_telegram_alert(user_id: str, alert_name: str, match_value: str, ad_count: int, ad_ids: list[str]):
    async with async_session() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user or not user.telegram_enabled or not user.telegram_chat_id:
            return

        # Get ad previews
        ads_preview = []
        if ad_ids:
            result = await db.execute(select(Ad).where(Ad.id.in_(ad_ids[:5])))
            for ad in result.scalars().all():
                ads_preview.append({
                    "headline": ad.headline or (ad.body_text[:60] if ad.body_text else "N/A"),
                    "platform": ad.platform,
                })

        text = build_alert_message(alert_name, match_value, ad_count, ads_preview)
        await send_telegram_message(user.telegram_chat_id, text)
