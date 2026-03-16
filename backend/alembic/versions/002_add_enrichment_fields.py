"""add enrichment fields

Revision ID: 002_enrichment
Revises: 001_initial
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_enrichment"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Auto-categorizer fields
    op.add_column("ads", sa.Column("category_l1", sa.String(100), index=True))
    op.add_column("ads", sa.Column("category_l2", sa.String(100), index=True))
    op.add_column("ads", sa.Column("detected_offers", postgresql.JSONB()))
    op.add_column("ads", sa.Column("emotional_triggers", postgresql.JSONB()))
    op.add_column("ads", sa.Column("target_audience_guess", sa.String(500)))

    # Spend estimation fields
    op.add_column("ads", sa.Column("estimated_daily_spend", sa.Float()))
    op.add_column("ads", sa.Column("estimated_total_spend", sa.Float()))
    op.add_column("ads", sa.Column("cpm_estimate", sa.Float()))
    op.add_column("ads", sa.Column("engagement_rate", sa.Float()))
    op.add_column("ads", sa.Column("viral_score", sa.Float()))
    op.add_column("ads", sa.Column("is_hot", sa.Boolean(), server_default="false", index=True))


def downgrade() -> None:
    op.drop_column("ads", "is_hot")
    op.drop_column("ads", "viral_score")
    op.drop_column("ads", "engagement_rate")
    op.drop_column("ads", "cpm_estimate")
    op.drop_column("ads", "estimated_total_spend")
    op.drop_column("ads", "estimated_daily_spend")
    op.drop_column("ads", "target_audience_guess")
    op.drop_column("ads", "emotional_triggers")
    op.drop_column("ads", "detected_offers")
    op.drop_column("ads", "category_l2")
    op.drop_column("ads", "category_l1")
