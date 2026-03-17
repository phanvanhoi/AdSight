"""add collection_count and content_hash to ads

Revision ID: 010_collection_tracking
Revises: 009_daily_digest
"""
from alembic import op
import sqlalchemy as sa

revision = "010_collection_tracking"
down_revision = "009_daily_digest"


def upgrade():
    op.add_column("ads", sa.Column("collection_count", sa.Integer(), server_default="1", nullable=True))
    op.add_column("ads", sa.Column("content_hash", sa.String(64), nullable=True))
    op.create_index("ix_ads_content_hash", "ads", ["content_hash"])


def downgrade():
    op.drop_index("ix_ads_content_hash", table_name="ads")
    op.drop_column("ads", "content_hash")
    op.drop_column("ads", "collection_count")
