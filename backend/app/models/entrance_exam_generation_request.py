import uuid
from app.core.time import utcnow

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class EntranceExamGenerationRequest(Base):
    """Append-only log for the entrance-exam generation rate limit -- exact
    mirror of TutorRequest, but kept as a separate table/budget so
    generating entrance-exam questions doesn't eat a student's tutor-chat
    quota (or vice versa)."""
    __tablename__ = "entrance_exam_generation_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
