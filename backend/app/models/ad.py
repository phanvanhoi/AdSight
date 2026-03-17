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

    # Enrichment — Auto-categorizer
    category_l1: Mapped[str | None] = mapped_column(String(100), index=True)
    category_l2: Mapped[str | None] = mapped_column(String(100), index=True)
    detected_offers: Mapped[dict | None] = mapped_column(JSONB, default=None)
    emotional_triggers: Mapped[dict | None] = mapped_column(JSONB, default=None)
    target_audience_guess: Mapped[str | None] = mapped_column(String(500))

    # Enrichment — Spend estimation
    estimated_daily_spend: Mapped[float | None] = mapped_column(Float)
    estimated_total_spend: Mapped[float | None] = mapped_column(Float)
    cpm_estimate: Mapped[float | None] = mapped_column(Float)
    engagement_rate: Mapped[float | None] = mapped_column(Float)
    viral_score: Mapped[float | None] = mapped_column(Float)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Creative metadata (populated by creative downloader)
    creative_s3_key: Mapped[str | None] = mapped_column(String(500))
    creative_file_size: Mapped[int | None] = mapped_column(Integer)
    creative_width: Mapped[int | None] = mapped_column(Integer)
    creative_height: Mapped[int | None] = mapped_column(Integer)
    creative_format: Mapped[str | None] = mapped_column(String(20))
    creative_duration: Mapped[float | None] = mapped_column(Float)
    creative_phash: Mapped[str | None] = mapped_column(String(64), index=True)
    has_text_overlay: Mapped[bool | None] = mapped_column(Boolean)
    dominant_colors: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # AI Analysis (on-demand, cached)
    ai_analysis: Mapped[dict | None] = mapped_column(JSONB, default=None)
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Collection tracking
    collection_count: Mapped[int] = mapped_column(Integer, default=1)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # Status
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
