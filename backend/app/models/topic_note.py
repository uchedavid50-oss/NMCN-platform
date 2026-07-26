import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.time import utcnow
from app.db.session import Base


class TopicNote(Base):
    """A single AI-generated study note per topic. One note per topic --
    regenerating replaces the existing note rather than creating duplicates."""
    __tablename__ = "topic_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, unique=True)
    content = Column(Text, nullable=False)  # markdown, may include ```mermaid blocks for diagrams
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    topic = relationship("Topic")