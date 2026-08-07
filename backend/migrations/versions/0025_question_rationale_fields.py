"""add rationale fields to questions and pending_questions

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("questions", "pending_questions"):
        op.add_column(table, sa.Column("why_others_wrong", sa.Text(), nullable=True))
        op.add_column(table, sa.Column("clinical_tip", sa.Text(), nullable=True))
        op.add_column(table, sa.Column("exam_specific_tip", sa.Text(), nullable=True))
        op.add_column(table, sa.Column("cognitive_level", sa.String(), nullable=True))


def downgrade() -> None:
    for table in ("questions", "pending_questions"):
        op.drop_column(table, "cognitive_level")
        op.drop_column(table, "exam_specific_tip")
        op.drop_column(table, "clinical_tip")
        op.drop_column(table, "why_others_wrong")
