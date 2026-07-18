"""add clinical case simulator tables

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject_context", sa.String(), nullable=True),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_clinical_cases_user_id", "clinical_cases", ["user_id"])

    op.create_table(
        "clinical_case_decision_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_clinical_case_decision_points_case_id", "clinical_case_decision_points", ["case_id"]
    )

    op.create_table(
        "clinical_case_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "decision_point_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_case_decision_points.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rationale", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_clinical_case_options_decision_point_id", "clinical_case_options", ["decision_point_id"]
    )

    op.create_table(
        "clinical_case_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_decisions", sa.Integer(), nullable=False),
        sa.Column("correct_decisions", sa.Integer(), nullable=False),
        sa.Column("score_percentage", sa.Float(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_clinical_case_results_user_id", "clinical_case_results", ["user_id"])


def downgrade() -> None:
    op.drop_table("clinical_case_results")
    op.drop_table("clinical_case_options")
    op.drop_table("clinical_case_decision_points")
    op.drop_table("clinical_cases")
