import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class UploadedNote(Base):
    __tablename__ = "uploaded_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    generated_questions = relationship(
        "GeneratedQuestion", back_populates="note", cascade="all, delete-orphan"
    )
