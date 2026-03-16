from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
