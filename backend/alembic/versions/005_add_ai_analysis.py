"""add AI analysis field to ads

Revision ID: 005_ai_analysis
Revises: 004_stripe_fields
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "005_ai_analysis"
down_revision = "004_stripe_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ads", sa.Column("ai_analysis", JSONB, nullable=True))
    op.add_column("ads", sa.Column("ai_analyzed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("ads", "ai_analyzed_at")
    op.drop_column("ads", "ai_analysis")
