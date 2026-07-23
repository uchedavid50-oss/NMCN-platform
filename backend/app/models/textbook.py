import uuid

from sqlalchemy import Column, String, Integer, LargeBinary, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class Textbook(Base):
    __tablename__ = "textbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id = Column(
        UUID(as_uuid=True), ForeignKey("textbook_folders.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False, default="application/pdf")
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    folder = relationship("TextbookFolder", back_populates="textbooks")
