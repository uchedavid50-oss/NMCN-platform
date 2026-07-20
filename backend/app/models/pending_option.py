import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class PendingOption(Base):
    __tablename__ = "pending_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pending_question_id = Column(
        UUID(as_uuid=True), ForeignKey("pending_questions.id", ondelete="CASCADE"), nullable=False
    )
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    question = relationship("PendingQuestion", back_populates="options")
