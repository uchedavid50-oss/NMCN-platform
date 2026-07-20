"""add admin content pipeline tables

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False, server_default="textbook"),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "pending_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False, server_default="medium"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_pending_questions_topic_id", "pending_questions", ["topic_id"])
    op.create_index("ix_pending_questions_status", "pending_questions", ["status"])

    op.create_table(
        "pending_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "pending_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pending_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_pending_options_pending_question_id", "pending_options", ["pending_question_id"])


def downgrade() -> None:
    op.drop_table("pending_options")
    op.drop_table("pending_questions")
    op.drop_table("admin_documents")
