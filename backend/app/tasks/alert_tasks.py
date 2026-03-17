"""Celery task — check competitor alerts and create notifications."""
import asyncio
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select, or_

from app.core.database import async_session
from app.models.ad import Ad
from app.models.competitor_alert import CompetitorAlert
from app.models.notification import Notification


@shared_task(name="check_competitor_ads")
def check_competitor_ads():
    """Chạy mỗi 2h — check all active alerts for new ads."""
    asyncio.run(_check_all_alerts())


async def _check_all_alerts():
    async with async_session() as db:
        result = await db.execute(
            select(CompetitorAlert).where(CompetitorAlert.is_active == True)  # noqa: E712
        )
        alerts = result.scalars().all()

        for alert in alerts:
            try:
                await _check_single_alert(alert, db)
            except Exception as e:
                print(f"Alert check failed for {alert.id}: {e}")

        await db.commit()


async def _check_single_alert(alert: CompetitorAlert, db):
    """Check 1 alert for new ads since last_checked."""
    since = alert.last_checked or alert.created_at
    now = datetime.now(timezone.utc)

    # Build query based on alert_type
    stmt = select(Ad).where(Ad.first_seen > since)

    if alert.alert_type == "advertiser_name":
        stmt = stmt.where(Ad.advertiser_name.ilike(f"%{alert.match_value}%"))
    elif alert.alert_type == "advertiser_group":
        from app.models.advertiser_group import AdvertiserGroup
        group_result = await db.execute(
            select(AdvertiserGroup).where(AdvertiserGroup.id == alert.match_value)
        )
        group = group_result.scalar_one_or_none()
        if not group or not group.platform_ids:
            alert.last_checked = now
            return
        conditions = []
        for plat, ids in group.platform_ids.items():
            if ids:
                conditions.append((Ad.platform == plat) & (Ad.advertiser_id.in_(ids)))
        if not conditions:
            alert.last_checked = now
            return
        stmt = stmt.where(or_(*conditions))
    elif alert.alert_type == "keyword":
        stmt = stmt.where(
            or_(
                Ad.headline.ilike(f"%{alert.match_value}%"),
                Ad.body_text.ilike(f"%{alert.match_value}%"),
            )
        )

    # Platform filter
    if alert.platforms:
        stmt = stmt.where(Ad.platform.in_(alert.platforms))

    result = await db.execute(stmt)
    new_ads = result.scalars().all()

    # Update alert
    alert.last_checked = now
    alert.last_found_count = len(new_ads)
    alert.total_found += len(new_ads)

    # Create notification if new ads found
    if new_ads:
        ad_ids = [str(a.id) for a in new_ads[:20]]
        notification = Notification(
            user_id=alert.user_id,
            alert_id=alert.id,
            type="new_competitor_ads",
            title=f"{alert.name}: {len(new_ads)} quảng cáo mới",
            body=f"Phát hiện {len(new_ads)} ads mới từ \"{alert.match_value}\" trên {', '.join(alert.platforms) if alert.platforms else 'tất cả nền tảng'}.",
            data={"ad_ids": ad_ids, "count": len(new_ads), "alert_name": alert.name},
        )
        db.add(notification)

        # Send email notification
        from app.tasks.email_tasks import send_alert_email
        send_alert_email.delay(
            str(alert.user_id),
            alert.name,
            alert.match_value,
            len(new_ads),
            ad_ids,
        )

        # Send Telegram notification
        from app.tasks.telegram_tasks import send_telegram_alert
        send_telegram_alert.delay(
            str(alert.user_id),
            alert.name,
            alert.match_value,
            len(new_ads),
            ad_ids,
        )
