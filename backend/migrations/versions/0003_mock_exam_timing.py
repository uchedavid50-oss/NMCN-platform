"""add time_limit_minutes and expires_at to attempts for mock exam mode

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-12

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("time_limit_minutes", sa.Integer(), nullable=True))
    op.add_column("attempts", sa.Column("expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "expires_at")
    op.drop_column("attempts", "time_limit_minutes")
