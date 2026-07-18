import uuid

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class CBTExamSession(Base):
    """A full, mixed-subject CBT simulation — deliberately a separate model from
    Attempt (Module 4/5), because the semantics differ: a mock Attempt's
    "total_questions" is derived from however many questions exist for its one
    topic, but a CBT session samples a FIXED count across every subject at
    start time and must score against exactly those questions, not however
    many exist in the DB overall."""

    __tablename__ = "cbt_exam_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    question_count = Column(Integer, nullable=False)
    time_limit_minutes = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    score_percentage = Column(Float, nullable=True)

    answers = relationship("CBTExamAnswer", back_populates="session", cascade="all, delete-orphan")
