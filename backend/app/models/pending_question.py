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
    # JSON-encoded {"A": "...", "B": "...", ...} keyed by each incorrect option's
    # letter position among the four options (A = 1st listed, ... D = 4th).
    why_others_wrong = Column(Text, nullable=True)
    clinical_tip = Column(Text, nullable=True)
    # Holds NMCN-Tip or NCLEX-Tip content depending on the topic's subject.exam_type.
    exam_specific_tip = Column(Text, nullable=True)
    cognitive_level = Column(String, nullable=True)  # Knowledge | Application | Analysis
    status = Column(String, nullable=False, default="pending")  # pending | approved | rejected
    # Carries through to the real Question's `source` field on approval.
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    topic = relationship("Topic")
    options = relationship("PendingOption", back_populates="question", cascade="all, delete-orphan")
