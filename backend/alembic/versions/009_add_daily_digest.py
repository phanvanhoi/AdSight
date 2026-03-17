"""add daily_digest_enabled to users

Revision ID: 009_daily_digest
Revises: 008_telegram
"""
from alembic import op
import sqlalchemy as sa

revision = "009_daily_digest"
down_revision = "008_telegram"


def upgrade() -> None:
    op.add_column("users", sa.Column("daily_digest_enabled", sa.Boolean(), server_default="true", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "daily_digest_enabled")
