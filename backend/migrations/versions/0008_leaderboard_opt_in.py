"""add leaderboard opt-in and display name to users

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-18

"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("leaderboard_opt_in", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("users", sa.Column("display_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "display_name")
    op.drop_column("users", "leaderboard_opt_in")
