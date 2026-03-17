"""add email_alerts_enabled to users

Revision ID: 007_email_alerts
Revises: 006_alerts_notifications
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = "007_email_alerts"
down_revision = "006_alerts_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_alerts_enabled", sa.Boolean(), server_default="true", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "email_alerts_enabled")
