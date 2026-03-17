"""add stripe and usage tracking fields to users

Revision ID: 004_stripe_fields
Revises: 003_tasks_09_13
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = "004_stripe_fields"
down_revision = "003_tasks_09_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("payment_method", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("subscription_status", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("subscription_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("daily_search_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("daily_search_reset", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("ai_credits_used", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("ai_credits_reset", sa.DateTime(timezone=True), nullable=True))

    op.create_unique_constraint("uq_users_stripe_customer_id", "users", ["stripe_customer_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_stripe_customer_id", "users", type_="unique")
    op.drop_column("users", "ai_credits_reset")
    op.drop_column("users", "ai_credits_used")
    op.drop_column("users", "daily_search_reset")
    op.drop_column("users", "daily_search_count")
    op.drop_column("users", "subscription_end")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "payment_method")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
