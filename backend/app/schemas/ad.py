from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class AdDetailResponse(BaseModel):
    id: UUID
    platform: str
    platform_ad_id: str
    advertiser_id: str | None = None
    advertiser_name: str | None = None
    advertiser_page_url: str | None = None
    ad_type: str = "image"
    headline: str | None = None
    body_text: str | None = None
    cta_type: str | None = None
    media_urls: list | None = None
    thumbnail_url: str | None = None
    landing_page_url: str | None = None
    target_countries: list | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    target_gender: str | None = None
    target_interests: list | None = None
    impressions_lower: int | None = None
    impressions_upper: int | None = None
    spend_lower: float | None = None
    spend_upper: float | None = None
    likes: int | None = 0
    comments: int | None = 0
    shares: int | None = 0
    language: str | None = None
    category: str | None = None
    tags: list | None = None
    sentiment: float | None = None
    # Enrichment — Categorizer
    category_l1: str | None = None
    category_l2: str | None = None
    detected_offers: list | None = None
    emotional_triggers: list | None = None

    @field_validator("detected_offers", "emotional_triggers", mode="before")
    @classmethod
    def _coerce_to_list(cls, v):
        if isinstance(v, dict):
            return list(v.values()) if v else None
        return v
    target_audience_guess: str | None = None
    # Enrichment — Estimator
    estimated_daily_spend: float | None = None
    estimated_total_spend: float | None = None
    cpm_estimate: float | None = None
    engagement_rate: float | None = None
    viral_score: float | None = None
    is_hot: bool = False
    # Creative metadata
    creative_phash: str | None = None
    has_text_overlay: bool | None = None
    dominant_colors: list | None = None
    # Collection tracking
    collection_count: int = 1
    # Status
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
