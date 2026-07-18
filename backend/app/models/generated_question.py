import uuid

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class GeneratedQuestion(Base):
    """Deliberately a separate table from Question (the admin-vetted bank).
    AI-generated content from a student's own notes is never mixed into the
    shared question bank every student sees — it stays private to whoever
    uploaded the notes, and is clearly labeled as AI-generated, not officially
    reviewed. This is a safety decision, not just a data-modeling one: a wrong
    fact in a student's own notes (or a Gemini misread) should never propagate
    into content other students might see as authoritative.
    """

    __tablename__ = "generated_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_notes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stem = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False, default="medium")
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    note = relationship("UploadedNote", back_populates="generated_questions")
    options = relationship("GeneratedOption", back_populates="question", cascade="all, delete-orphan")
