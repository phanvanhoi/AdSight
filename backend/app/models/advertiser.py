from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Advertiser(BaseModel):
    __tablename__ = "advertisers"

    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_advertiser_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    page_url: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(10))
    total_ads: Mapped[int] = mapped_column(Integer, default=0)
    active_ads: Mapped[int] = mapped_column(Integer, default=0)
    estimated_monthly_spend: Mapped[float | None] = mapped_column(Float)
