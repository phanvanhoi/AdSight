"""Celery task — send alert emails."""
import asyncio

from celery import shared_task
from sqlalchemy import select

from app.core.database import async_session
from app.core.email import send_email
from app.core.email_templates import competitor_alert_email
from app.models.ad import Ad
from app.models.user import User


@shared_task(name="send_alert_email")
def send_alert_email(user_id: str, alert_name: str, match_value: str, ad_count: int, ad_ids: list[str]):
    """Send competitor alert email to user."""
    asyncio.run(_send_alert_email(user_id, alert_name, match_value, ad_count, ad_ids))


async def _send_alert_email(user_id: str, alert_name: str, match_value: str, ad_count: int, ad_ids: list[str]):
    async with async_session() as db:
        # Get user
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user or not user.email_alerts_enabled:
            return

        # Get ad previews
        ads_preview = []
        if ad_ids:
            result = await db.execute(select(Ad).where(Ad.id.in_(ad_ids[:5])))
            for ad in result.scalars().all():
                ads_preview.append({
                    "headline": ad.headline or (ad.body_text[:80] if ad.body_text else "N/A"),
                    "platform": ad.platform,
                    "ad_type": ad.ad_type,
                    "first_seen": str(ad.first_seen.date()) if ad.first_seen else "",
                })

        # Build and send email
        html = competitor_alert_email(alert_name, match_value, ad_count, ads_preview)
        subject = f"{alert_name}: {ad_count} quảng cáo mới — AdSight"
        send_email(user.email, subject, html)
