from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Ad(BaseModel):
    __tablename__ = "ads"
    __table_args__ = (
        UniqueConstraint("platform", "platform_ad_id", name="uq_ad_platform_id"),
    )

    # Platform identity
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_ad_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Advertiser
    advertiser_id: Mapped[str | None] = mapped_column(String(255), index=True)
    advertiser_name: Mapped[str | None] = mapped_column(String(500))
    advertiser_page_url: Mapped[str | None] = mapped_column(Text)

    # Creative
    ad_type: Mapped[str] = mapped_column(String(50), default="image")  # image, video, carousel, text
    headline: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    cta_type: Mapped[str | None] = mapped_column(String(100))
    media_urls: Mapped[dict | None] = mapped_column(JSONB, default=None)
    media_s3_keys: Mapped[dict | None] = mapped_column(JSONB, default=None)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    landing_page_url: Mapped[str | None] = mapped_column(Text)

    # Targeting
    target_countries: Mapped[dict | None] = mapped_column(JSONB, default=None)
    target_age_min: Mapped[int | None] = mapped_column(Integer)
    target_age_max: Mapped[int | None] = mapped_column(Integer)
    target_gender: Mapped[str | None] = mapped_column(String(20))
    target_interests: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # Performance
    impressions_lower: Mapped[int | None] = mapped_column(Integer)
    impressions_upper: Mapped[int | None] = mapped_column(Integer)
    spend_lower: Mapped[float | None] = mapped_column(Float)
    spend_upper: Mapped[float | None] = mapped_column(Float)
    likes: Mapped[int | None] = mapped_column(Integer, default=0)
    comments: Mapped[int | None] = mapped_column(Integer, default=0)
    shares: Mapped[int | None] = mapped_column(Integer, default=0)

    # Classification
    language: Mapped[str | None] = mapped_column(String(10))
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, default=None)
    sentiment: Mapped[float | None] = mapped_column(Float)

    # Status
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
