import uuid

from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ClinicalCaseDecisionPoint(Base):
    __tablename__ = "clinical_case_decision_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("clinical_cases.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)

    case = relationship("ClinicalCase", back_populates="decision_points")
    options = relationship(
        "ClinicalCaseOption", back_populates="decision_point", cascade="all, delete-orphan"
    )
