from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class SearchRequest(BaseModel):
    q: str = ""
    platform: str | None = None
    country: str | None = None
    ad_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    min_likes: int | None = None
    sort: str = "relevance"
    page: int = 1
    limit: int = 20


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


class Facets(BaseModel):
    platforms: dict[str, int] = {}
    ad_types: dict[str, int] = {}
    categories: dict[str, int] = {}


class SearchResponse(BaseModel):
    total: int
    page: int
    limit: int
    results: list[AdSummary]
    facets: Facets
