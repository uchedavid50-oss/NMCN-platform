"""add entrance_exam_questions and entrance_exam_generation_requests tables

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entrance_exam_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("question_type", sa.String(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("model_answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_entrance_exam_questions_subject", "entrance_exam_questions", ["subject"])
    op.create_table(
        "entrance_exam_generation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("entrance_exam_generation_requests")
    op.drop_index("ix_entrance_exam_questions_subject", table_name="entrance_exam_questions")
    op.drop_table("entrance_exam_questions")
