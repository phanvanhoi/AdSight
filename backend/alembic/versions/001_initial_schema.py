"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("tier", sa.String(50), server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- advertisers ---
    op.create_table(
        "advertisers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_advertiser_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("page_url", sa.Text()),
        sa.Column("website", sa.Text()),
        sa.Column("category", sa.String(255)),
        sa.Column("country", sa.String(10)),
        sa.Column("total_ads", sa.Integer(), server_default="0"),
        sa.Column("active_ads", sa.Integer(), server_default="0"),
        sa.Column("estimated_monthly_spend", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("platform", "platform_advertiser_id", name="uq_advertiser_platform_id"),
    )
    op.create_index("ix_advertisers_platform", "advertisers", ["platform"])
    op.create_index("ix_advertisers_platform_advertiser_id", "advertisers", ["platform_advertiser_id"])

    # --- ads ---
    op.create_table(
        "ads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_ad_id", sa.String(255), nullable=False),
        sa.Column("advertiser_id", sa.String(255)),
        sa.Column("advertiser_name", sa.String(500)),
        sa.Column("advertiser_page_url", sa.Text()),
        sa.Column("ad_type", sa.String(50), server_default="image"),
        sa.Column("headline", sa.Text()),
        sa.Column("body_text", sa.Text()),
        sa.Column("cta_type", sa.String(100)),
        sa.Column("media_urls", postgresql.JSONB()),
        sa.Column("media_s3_keys", postgresql.JSONB()),
        sa.Column("thumbnail_url", sa.Text()),
        sa.Column("landing_page_url", sa.Text()),
        sa.Column("target_countries", postgresql.JSONB()),
        sa.Column("target_age_min", sa.Integer()),
        sa.Column("target_age_max", sa.Integer()),
        sa.Column("target_gender", sa.String(20)),
        sa.Column("target_interests", postgresql.JSONB()),
        sa.Column("impressions_lower", sa.Integer()),
        sa.Column("impressions_upper", sa.Integer()),
        sa.Column("spend_lower", sa.Float()),
        sa.Column("spend_upper", sa.Float()),
        sa.Column("likes", sa.Integer(), server_default="0"),
        sa.Column("comments", sa.Integer(), server_default="0"),
        sa.Column("shares", sa.Integer(), server_default="0"),
        sa.Column("language", sa.String(10)),
        sa.Column("category", sa.String(255)),
        sa.Column("tags", postgresql.JSONB()),
        sa.Column("sentiment", sa.Float()),
        sa.Column("first_seen", sa.DateTime(timezone=True)),
        sa.Column("last_seen", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("platform", "platform_ad_id", name="uq_ad_platform_id"),
    )
    op.create_index("ix_ads_platform", "ads", ["platform"])
    op.create_index("ix_ads_platform_ad_id", "ads", ["platform_ad_id"])
    op.create_index("ix_ads_advertiser_id", "ads", ["advertiser_id"])
    op.create_index("ix_ads_category", "ads", ["category"])
    op.create_index("ix_ads_is_active", "ads", ["is_active"])

    # --- boards ---
    op.create_table(
        "boards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_boards_user_id", "boards", ["user_id"])

    # --- board_ads ---
    op.create_table(
        "board_ads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("boards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ad_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("board_id", "ad_id", name="uq_board_ad"),
    )
    op.create_index("ix_board_ads_board_id", "board_ads", ["board_id"])
    op.create_index("ix_board_ads_ad_id", "board_ads", ["ad_id"])


def downgrade() -> None:
    op.drop_table("board_ads")
    op.drop_table("boards")
    op.drop_table("ads")
    op.drop_table("advertisers")
    op.drop_table("users")
