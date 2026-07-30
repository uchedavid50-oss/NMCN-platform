import uuid
from sqlalchemy import Column, String, Text, Integer, LargeBinary, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.time import utcnow
from app.db.session import Base


class EquipmentContent(Base):
    """Singleton row: one video + one PDF covering all nursing equipment
    for the Viva section. There is only ever one row -- fetched via
    get-or-create rather than keyed by any parent record."""
    __tablename__ = "equipment_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, default="Nursing Equipment")
    description = Column(Text, nullable=False, default="")
    youtube_url = Column(Text, nullable=True)
    pdf_filename = Column(String, nullable=True)
    pdf_content_type = Column(String, nullable=True)
    pdf_data = Column(LargeBinary, nullable=True)
    pdf_size = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
