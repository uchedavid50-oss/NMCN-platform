import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class PendingQuestion(Base):
    __tablename__ = "pending_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("admin_documents.id", ondelete="SET NULL"), nullable=True
    )
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    stem = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False, default="medium")
    explanation = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending | approved | rejected
    created_at = Column(DateTime, default=utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    options = relationship("PendingOption", back_populates="question", cascade="all, delete-orphan")
