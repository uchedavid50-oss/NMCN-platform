import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.time import utcnow
from app.db.session import Base


class EntranceExamQuestion(Base):
    """AI-generated past-question-bank entry for the Nursing Entrance Exam
    section. Not tied to the nursing curriculum's Subject/Topic tables --
    `subject` is one of a fixed set of pre-nursing academic subjects
    (Biology, Chemistry, Current Affairs, English, Mathematics, Physics),
    validated in the API schema rather than as a DB enum. Short-answer/
    fill-in-blank/theory only, no options -- students self-check against
    `model_answer` rather than picking from choices."""
    __tablename__ = "entrance_exam_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String, nullable=False, index=True)
    question_type = Column(String, nullable=False)  # short_answer | fill_blank | theory
    question_text = Column(Text, nullable=False)
    model_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
