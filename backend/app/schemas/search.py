from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    q: str = ""
    platform: str | None = None
    country: str | None = None
    ad_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    min_likes: int | None = None
    category_l1: str | None = None
    category_l2: str | None = None
    min_spend: float | None = None
    max_spend: float | None = None
    min_viral_score: float | None = None
    is_hot: bool | None = None
    has_discount: bool | None = None
    sort: str = "relevance"
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class AdSummary(BaseModel):
    id: str
    platform: str
    advertiser_name: str | None = None
    ad_type: str = "image"
    headline: str | None = None
    body_text: str | None = None
    thumbnail_url: str | None = None
    cta_type: str | None = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    first_seen: str | None = None
    last_seen: str | None = None
    is_active: bool = True
    days_running: int = 0
    category_l1: str | None = None
    category_l2: str | None = None
    viral_score: float | None = None
    is_hot: bool = False


class Facets(BaseModel):
    platforms: dict[str, int] = {}
    ad_types: dict[str, int] = {}
    categories: dict[str, int] = {}
    categories_l1: dict[str, int] = {}


class ExportSearchRequest(SearchRequest):
    """SearchRequest variant for export — no upper limit on results."""
    limit: int = Field(default=100, ge=1)


class SearchResponse(BaseModel):
    total: int
    page: int
    limit: int
    results: list[AdSummary]
    facets: Facets
