from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    alert_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("competitor_alerts.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # new_competitor_ads, system, billing
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, default=None)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user = relationship("User")
    alert = relationship("CompetitorAlert")
