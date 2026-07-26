"""add source column to questions and pending_questions

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("source", sa.String(), nullable=True))
    op.add_column("pending_questions", sa.Column("source", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("pending_questions", "source")
    op.drop_column("questions", "source")
