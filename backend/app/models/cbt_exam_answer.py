import uuid

from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class CBTExamAnswer(Base):
    __tablename__ = "cbt_exam_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("cbt_exam_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_id = Column(UUID(as_uuid=True), ForeignKey("options.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, nullable=False)

    session = relationship("CBTExamSession", back_populates="answers")
