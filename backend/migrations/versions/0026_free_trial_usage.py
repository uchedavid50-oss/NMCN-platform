"""add free_trial_usage table

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "free_trial_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("feature", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_free_trial_usage_user_feature", "free_trial_usage", ["user_id", "feature"])


def downgrade() -> None:
    op.drop_index("ix_free_trial_usage_user_feature", table_name="free_trial_usage")
    op.drop_table("free_trial_usage")
