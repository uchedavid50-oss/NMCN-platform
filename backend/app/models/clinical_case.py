import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class ClinicalCase(Base):
    """AI-generated patient case scenario. Private to whoever generated it,
    same reasoning as generated_questions (Module 22) — unreviewed AI content
    stays out of anything shared/official."""

    __tablename__ = "clinical_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_context = Column(String, nullable=True)  # display label only, e.g. "Medical-Surgical Nursing"
    scenario = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    decision_points = relationship(
        "ClinicalCaseDecisionPoint",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="ClinicalCaseDecisionPoint.order_index",
    )
