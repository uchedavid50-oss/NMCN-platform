import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.time import utcnow
from app.db.session import Base


class OrganVideo(Base):
    """Admin-assigned YouTube video for a single organ on the Viva Organs
    page. One video per organ -- saving again replaces the existing URL."""
    __tablename__ = "organ_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organ_id = Column(UUID(as_uuid=True), ForeignKey("organs.id", ondelete="CASCADE"), nullable=False, unique=True)
    youtube_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organ = relationship("Organ")
