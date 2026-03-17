"""add competitor_alerts and notifications tables

Revision ID: 006_alerts_notifications
Revises: 005_ai_analysis
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "006_alerts_notifications"
down_revision = "005_ai_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competitor_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("match_value", sa.String(500), nullable=False),
        sa.Column("platforms", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_found_count", sa.Integer(), server_default="0"),
        sa.Column("total_found", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("alert_id", UUID(as_uuid=True), sa.ForeignKey("competitor_alerts.id"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("data", JSONB, nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("competitor_alerts")
