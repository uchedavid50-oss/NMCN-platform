"""add provider column to entrance_exam_questions

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("entrance_exam_questions", sa.Column("provider", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("entrance_exam_questions", "provider")
