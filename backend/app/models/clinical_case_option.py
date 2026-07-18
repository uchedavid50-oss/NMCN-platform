import uuid

from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ClinicalCaseOption(Base):
    __tablename__ = "clinical_case_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_point_id = Column(
        UUID(as_uuid=True), ForeignKey("clinical_case_decision_points.id", ondelete="CASCADE"), nullable=False
    )
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)
    rationale = Column(Text, nullable=False)

    decision_point = relationship("ClinicalCaseDecisionPoint", back_populates="options")
