from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AdvertiserGroup(BaseModel):
    __tablename__ = "advertiser_groups"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    platform_ids: Mapped[dict | None] = mapped_column(JSONB, default=None)
    total_ads: Mapped[int] = mapped_column(Integer, default=0)
    total_estimated_spend: Mapped[float] = mapped_column(Float, default=0.0)
    categories: Mapped[dict | None] = mapped_column(JSONB, default=None)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
