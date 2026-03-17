from datetime import datetime

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CompetitorAlert(BaseModel):
    __tablename__ = "competitor_alerts"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # advertiser_name, advertiser_group, keyword
    match_value: Mapped[str] = mapped_column(String(500), nullable=False)
    platforms: Mapped[dict | None] = mapped_column(JSONB, default=None)  # ["meta","tiktok"] or null=all
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_found_count: Mapped[int] = mapped_column(Integer, default=0)
    total_found: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="alerts")
