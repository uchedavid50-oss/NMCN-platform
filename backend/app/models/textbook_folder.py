import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class TextbookFolder(Base):
    __tablename__ = "textbook_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=utcnow)

    textbooks = relationship("Textbook", back_populates="folder", cascade="all, delete-orphan")
