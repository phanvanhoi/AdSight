from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LandingPageInfo(BaseModel):
    __tablename__ = "landing_page_info"

    ad_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ads.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    final_url: Mapped[str | None] = mapped_column(Text)
    redirect_chain: Mapped[dict | None] = mapped_column(JSONB, default=None)
    platform_detected: Mapped[str | None] = mapped_column(String(50), index=True)
    product_name: Mapped[str | None] = mapped_column(String(500))
    product_price: Mapped[float | None] = mapped_column(Float)
    product_currency: Mapped[str | None] = mapped_column(String(10), default="VND")
    product_image_url: Mapped[str | None] = mapped_column(Text)
    has_fb_pixel: Mapped[bool] = mapped_column(Boolean, default=False)
    has_tiktok_pixel: Mapped[bool] = mapped_column(Boolean, default=False)
    has_google_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    has_chat_widget: Mapped[str | None] = mapped_column(String(50))
    has_ssl: Mapped[bool] = mapped_column(Boolean, default=False)
    page_load_ms: Mapped[int | None] = mapped_column(Integer)
    screenshot_s3_key: Mapped[str | None] = mapped_column(String(500))
    crawl_status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
