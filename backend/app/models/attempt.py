import uuid
from app.core.time import utcnow

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String, nullable=False, default="practice")  # practice | mock
    started_at = Column(DateTime, default=utcnow)
    finished_at = Column(DateTime, nullable=True)
    score_percentage = Column(Float, nullable=True)

    # Mock-exam only fields (null for practice attempts)
    time_limit_minutes = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")
