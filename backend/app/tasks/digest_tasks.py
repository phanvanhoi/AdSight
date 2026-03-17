"""Celery task — send daily digest emails."""
import asyncio
from datetime import datetime, timezone, timedelta

from celery import shared_task
from sqlalchemy import select, func

from app.core.database import async_session
from app.core.email import send_email
from app.core.email_templates import daily_digest_email
from app.models.ad import Ad
from app.models.notification import Notification
from app.models.user import User


@shared_task(name="send_daily_digest")
def send_daily_digest():
    """Gửi daily digest cho tất cả eligible users."""
    asyncio.run(_send_all_digests())


async def _send_all_digests():
    async with async_session() as db:
        # Get eligible users (paid + digest enabled + email alerts enabled)
        result = await db.execute(
            select(User).where(
                User.tier != "free",
                User.daily_digest_enabled == True,  # noqa: E712
                User.email_alerts_enabled == True,  # noqa: E712
            )
        )
        users = result.scalars().all()

        if not users:
            print("No eligible users for daily digest")
            return

        # Get trending ads (last 24h, top by viral_score)
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        trending_result = await db.execute(
            select(Ad)
            .where(Ad.first_seen > yesterday)
            .order_by(Ad.viral_score.desc().nulls_last())
            .limit(10)
        )
        trending_ads = trending_result.scalars().all()

        # Get global stats
        total_new = await db.scalar(
            select(func.count()).select_from(Ad).where(Ad.first_seen > yesterday)
        ) or 0

        # Top category
        top_category = trending_ads[0].category_l1 if trending_ads and trending_ads[0].category_l1 else "N/A"

        stats = {
            "total_new_ads": total_new,
            "top_category": top_category,
            "most_active_platform": trending_ads[0].platform if trending_ads else "N/A",
        }

        trending_data = [
            {
                "id": str(a.id),
                "headline": a.headline or (a.body_text[:60] if a.body_text else "N/A"),
                "platform": a.platform,
                "likes": a.likes or 0,
                "viral_score": a.viral_score or 0,
            }
            for a in trending_ads[:5]
        ]

        date_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        sent_count = 0

        for user in users:
            try:
                # Get user's competitor updates (notifications from last 24h)
                notif_result = await db.execute(
                    select(Notification).where(
                        Notification.user_id == user.id,
                        Notification.type == "new_competitor_ads",
                        Notification.created_at > yesterday,
                    )
                )
                notifications = notif_result.scalars().all()
                competitor_updates = [
                    {
                        "alert_name": n.data.get("alert_name", "Alert") if n.data else "Alert",
                        "count": n.data.get("count", 0) if n.data else 0,
                    }
                    for n in notifications
                ]

                html = daily_digest_email(
                    user_name=user.full_name,
                    date_str=date_str,
                    trending_ads=trending_data,
                    competitor_updates=competitor_updates,
                    stats=stats,
                )
                subject = f"AdSight Daily Digest — {date_str}"
                send_email(user.email, subject, html)
                sent_count += 1
            except Exception as e:
                print(f"Digest failed for {user.email}: {e}")

        print(f"Daily digest sent to {sent_count}/{len(users)} users")
