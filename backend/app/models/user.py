from datetime import datetime

from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tier: Mapped[str] = mapped_column(String(50), default="free")  # free, pro, agency

    # Payment
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "stripe", "vnpay", "momo"
    subscription_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # active, canceled, past_due, expired
    subscription_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Settings
    email_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Telegram
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Usage tracking
    daily_search_count: Mapped[int] = mapped_column(Integer, default=0)
    daily_search_reset: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_credits_used: Mapped[int] = mapped_column(Integer, default=0)
    ai_credits_reset: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    boards: Mapped[list["Board"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list["CompetitorAlert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
