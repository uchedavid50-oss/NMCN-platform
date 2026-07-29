import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.time import utcnow
from app.db.session import Base


class TopicVideo(Base):
    """Admin-assigned YouTube demonstration video for an OSCE procedure
    topic. One video per topic -- saving again replaces the existing URL
    rather than creating duplicates."""
    __tablename__ = "topic_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, unique=True)
    youtube_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    topic = relationship("Topic")
