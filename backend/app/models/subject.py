import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    exam_type = Column(String, nullable=False, default="NMCN")  # "NMCN" | "NCLEX"

    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
