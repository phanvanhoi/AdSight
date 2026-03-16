from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class TikTokShop(BaseModel):
    __tablename__ = "tiktok_shops"

    shop_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    shop_name: Mapped[str] = mapped_column(String(500), nullable=False)
    shop_url: Mapped[str | None] = mapped_column(Text)
    followers: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float | None] = mapped_column(Float)
    total_products: Mapped[int] = mapped_column(Integer, default=0)
    total_sales: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    products: Mapped[list["TikTokShopProduct"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )


class TikTokShopProduct(BaseModel):
    __tablename__ = "tiktok_shop_products"

    product_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_url: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="VND")
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float | None] = mapped_column(Float)
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    images: Mapped[dict | None] = mapped_column(JSONB, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Sales tracking over time
    daily_sales: Mapped[dict | None] = mapped_column(JSONB, default=None)
    estimated_daily_revenue: Mapped[float | None] = mapped_column(Float)
    estimated_monthly_revenue: Mapped[float | None] = mapped_column(Float)

    # Shop FK
    shop_id_fk: Mapped[str] = mapped_column(
        "shop_id_fk",
        UUID(as_uuid=True),
        ForeignKey("tiktok_shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop: Mapped["TikTokShop"] = relationship(back_populates="products")
