"""add tutor_requests table for rate limiting

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tutor_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tutor_requests_user_id", "tutor_requests", ["user_id"])
    op.create_index("ix_tutor_requests_created_at", "tutor_requests", ["created_at"])


def downgrade() -> None:
    op.drop_table("tutor_requests")
