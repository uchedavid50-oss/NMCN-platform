import uuid

from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base


class SpeedRoundResult(Base):
    __tablename__ = "speed_round_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    played_at = Column(DateTime, default=utcnow, nullable=False)
