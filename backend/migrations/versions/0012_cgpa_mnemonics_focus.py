"""add courses, mnemonics, focus_sessions tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("semester", sa.String(), nullable=False),
        sa.Column("course_name", sa.String(), nullable=False),
        sa.Column("credit_units", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_courses_user_id", "courses", ["user_id"])

    op.create_table(
        "mnemonics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("mnemonic_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_mnemonics_user_id", "mnemonics", ["user_id"])

    op.create_table(
        "focus_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_focus_sessions_user_id", "focus_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_table("focus_sessions")
    op.drop_table("mnemonics")
    op.drop_table("courses")
