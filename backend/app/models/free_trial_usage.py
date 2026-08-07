import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base


class FreeTrialUsage(Base):
    """One row per free-trial attempt at a feature that has no other
    persisted "session started" record of its own (flashcards, speed round,
    past-questions). Practice, mock, CBT, and clinical cases reuse their
    existing Attempt/CBTExamSession/ClinicalCase rows instead of this table."""

    __tablename__ = "free_trial_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String, nullable=False)  # "flashcards" | "speed_round" | "past_questions"
    created_at = Column(DateTime, default=utcnow, nullable=False)
