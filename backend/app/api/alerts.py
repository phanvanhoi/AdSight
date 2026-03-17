from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.tier_limits import get_tier_limits
from app.dependencies import get_current_user
from app.models.competitor_alert import CompetitorAlert
from app.models.user import User

router = APIRouter()


class AlertCreate(BaseModel):
    name: str
    alert_type: str  # advertiser_name, advertiser_group, keyword
    match_value: str
    platforms: list[str] | None = None


class AlertUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    platforms: list[str] | None = None


@router.get("")
async def list_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetitorAlert)
        .where(CompetitorAlert.user_id == user.id)
        .order_by(CompetitorAlert.created_at.desc())
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "alert_type": a.alert_type,
            "match_value": a.match_value,
            "platforms": a.platforms,
            "is_active": a.is_active,
            "last_checked": str(a.last_checked) if a.last_checked else None,
            "last_found_count": a.last_found_count,
            "total_found": a.total_found,
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Enforce tier limit
    limits = get_tier_limits(user.tier)
    if limits.max_alerts == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "alerts_not_available",
                "message": "Competitor alerts chỉ có trong gói Pro trở lên.",
                "upgrade_url": "/pricing",
            },
        )

    count = await db.scalar(
        select(func.count()).select_from(CompetitorAlert).where(
            CompetitorAlert.user_id == user.id
        )
    )
    if count >= limits.max_alerts:
        raise HTTPException(
            status_code=403,
            detail=f"Gói {user.tier} chỉ được tạo {limits.max_alerts} alerts. Nâng cấp để tạo thêm.",
        )

    # Validate alert_type
    if data.alert_type not in ("advertiser_name", "advertiser_group", "keyword"):
        raise HTTPException(status_code=400, detail="Invalid alert_type")

    alert = CompetitorAlert(
        user_id=user.id,
        name=data.name,
        alert_type=data.alert_type,
        match_value=data.match_value,
        platforms=data.platforms,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return {"id": str(alert.id), "name": alert.name, "alert_type": alert.alert_type}


@router.patch("/{alert_id}")
async def update_alert(
    alert_id: UUID,
    data: AlertUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetitorAlert).where(
            CompetitorAlert.id == alert_id,
            CompetitorAlert.user_id == user.id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if data.name is not None:
        alert.name = data.name
    if data.is_active is not None:
        alert.is_active = data.is_active
    if data.platforms is not None:
        alert.platforms = data.platforms

    await db.commit()
    return {"id": str(alert.id), "name": alert.name, "is_active": alert.is_active}


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetitorAlert).where(
            CompetitorAlert.id == alert_id,
            CompetitorAlert.user_id == user.id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
