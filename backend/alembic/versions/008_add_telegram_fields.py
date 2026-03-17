"""add telegram fields to users

Revision ID: 008_telegram
Revises: 007_email_alerts
"""
from alembic import op
import sqlalchemy as sa

revision = "008_telegram"
down_revision = "007_email_alerts"


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.String(50), unique=True, nullable=True))
    op.add_column("users", sa.Column("telegram_enabled", sa.Boolean(), server_default="false", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "telegram_enabled")
    op.drop_column("users", "telegram_chat_id")
