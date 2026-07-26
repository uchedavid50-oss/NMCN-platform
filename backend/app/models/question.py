import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
class Question(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    stem = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False, default="medium")  # easy | medium | hard
    explanation = Column(Text, nullable=False)
    # Tags where this question actually came from -- "past_questions" for
    # ones generated from real past-exam documents, None/other for regular
    # admin-curated content. Lets students browse past-questions-derived
    # content specifically via its own dedicated page.
    source = Column(String, nullable=True)
    topic = relationship("Topic", back_populates="questions")
    options = relationship("Option", back_populates="question", cascade="all, delete-orphan")
