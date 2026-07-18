import uuid

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base


class ClinicalCaseResult(Base):
    __tablename__ = "clinical_case_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("clinical_cases.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_decisions = Column(Integer, nullable=False)
    correct_decisions = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    completed_at = Column(DateTime, default=utcnow, nullable=False)
