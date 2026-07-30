"""add viva tables: equipment_content, organs, organ_videos

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipment_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("youtube_url", sa.Text(), nullable=True),
        sa.Column("pdf_filename", sa.String(), nullable=True),
        sa.Column("pdf_content_type", sa.String(), nullable=True),
        sa.Column("pdf_data", sa.LargeBinary(), nullable=True),
        sa.Column("pdf_size", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "organs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "organ_videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organ_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("youtube_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("organ_videos")
    op.drop_table("organs")
    op.drop_table("equipment_content")
