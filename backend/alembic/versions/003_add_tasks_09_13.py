"""add landing pages, tiktok shop, advertiser groups, creative fields

Revision ID: 003_tasks_09_13
Revises: 002_enrichment
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_tasks_09_13"
down_revision = "002_enrichment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Creative fields on ads table ---
    op.add_column("ads", sa.Column("creative_s3_key", sa.String(500)))
    op.add_column("ads", sa.Column("creative_file_size", sa.Integer()))
    op.add_column("ads", sa.Column("creative_width", sa.Integer()))
    op.add_column("ads", sa.Column("creative_height", sa.Integer()))
    op.add_column("ads", sa.Column("creative_format", sa.String(20)))
    op.add_column("ads", sa.Column("creative_duration", sa.Float()))
    op.add_column("ads", sa.Column("creative_phash", sa.String(64), index=True))
    op.add_column("ads", sa.Column("has_text_overlay", sa.Boolean()))
    op.add_column("ads", sa.Column("dominant_colors", postgresql.JSONB()))

    # --- Landing page info table ---
    op.create_table(
        "landing_page_info",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ad_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ads.id", ondelete="CASCADE"),
                   unique=True, nullable=False, index=True),
        sa.Column("final_url", sa.Text()),
        sa.Column("redirect_chain", postgresql.JSONB()),
        sa.Column("platform_detected", sa.String(50), index=True),
        sa.Column("product_name", sa.String(500)),
        sa.Column("product_price", sa.Float()),
        sa.Column("product_currency", sa.String(10), server_default="VND"),
        sa.Column("product_image_url", sa.Text()),
        sa.Column("has_fb_pixel", sa.Boolean(), server_default="false"),
        sa.Column("has_tiktok_pixel", sa.Boolean(), server_default="false"),
        sa.Column("has_google_analytics", sa.Boolean(), server_default="false"),
        sa.Column("has_chat_widget", sa.String(50)),
        sa.Column("has_ssl", sa.Boolean(), server_default="false"),
        sa.Column("page_load_ms", sa.Integer()),
        sa.Column("screenshot_s3_key", sa.String(500)),
        sa.Column("crawl_status", sa.String(20), server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column("crawled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- TikTok shops table ---
    op.create_table(
        "tiktok_shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shop_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("shop_name", sa.String(500), nullable=False),
        sa.Column("shop_url", sa.Text()),
        sa.Column("followers", sa.Integer(), server_default="0"),
        sa.Column("rating", sa.Float()),
        sa.Column("total_products", sa.Integer(), server_default="0"),
        sa.Column("total_sales", sa.Integer()),
        sa.Column("category", sa.String(255)),
        sa.Column("is_verified", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- TikTok shop products table ---
    op.create_table(
        "tiktok_shop_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("product_url", sa.Text()),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("original_price", sa.Float()),
        sa.Column("currency", sa.String(10), server_default="VND"),
        sa.Column("sales_count", sa.Integer(), server_default="0"),
        sa.Column("review_count", sa.Integer(), server_default="0"),
        sa.Column("rating", sa.Float()),
        sa.Column("category", sa.String(255), index=True),
        sa.Column("images", postgresql.JSONB()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("daily_sales", postgresql.JSONB()),
        sa.Column("estimated_daily_revenue", sa.Float()),
        sa.Column("estimated_monthly_revenue", sa.Float()),
        sa.Column("shop_id_fk", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("tiktok_shops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- Advertiser groups table ---
    op.create_table(
        "advertiser_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, index=True),
        sa.Column("platform_ids", postgresql.JSONB()),
        sa.Column("total_ads", sa.Integer(), server_default="0"),
        sa.Column("total_estimated_spend", sa.Float(), server_default="0"),
        sa.Column("categories", postgresql.JSONB()),
        sa.Column("is_verified", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("advertiser_groups")
    op.drop_table("tiktok_shop_products")
    op.drop_table("tiktok_shops")
    op.drop_table("landing_page_info")
    op.drop_column("ads", "dominant_colors")
    op.drop_column("ads", "has_text_overlay")
    op.drop_column("ads", "creative_phash")
    op.drop_column("ads", "creative_duration")
    op.drop_column("ads", "creative_format")
    op.drop_column("ads", "creative_height")
    op.drop_column("ads", "creative_width")
    op.drop_column("ads", "creative_file_size")
    op.drop_column("ads", "creative_s3_key")
