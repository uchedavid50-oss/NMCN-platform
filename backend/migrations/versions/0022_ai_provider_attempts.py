"""add ai_provider_attempts table

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_provider_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_ai_provider_attempts_provider", "ai_provider_attempts", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_ai_provider_attempts_provider", table_name="ai_provider_attempts")
    op.drop_table("ai_provider_attempts")
