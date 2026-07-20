import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base


class AdminDocument(Base):
    """Admin-uploaded source material — textbooks or past question sets —
    used to generate pending questions for review. Deliberately never exposed
    to students directly; only the questions generated from it (after admin
    approval) ever become visible."""

    __tablename__ = "admin_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=False, default="textbook")  # textbook | past_questions | other
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
