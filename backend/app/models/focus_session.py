import uuid

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base


class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    completed_at = Column(DateTime, default=utcnow, nullable=False)
