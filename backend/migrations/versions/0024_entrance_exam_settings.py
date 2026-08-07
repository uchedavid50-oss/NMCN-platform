"""add entrance_exam_settings table

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entrance_exam_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("free_questions_per_subject", sa.Integer(), nullable=False, server_default="10"),
    )
    op.execute(
        "INSERT INTO entrance_exam_settings (id, free_questions_per_subject) VALUES (1, 10)"
    )


def downgrade() -> None:
    op.drop_table("entrance_exam_settings")
