import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base


class Mnemonic(Base):
    __tablename__ = "mnemonics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    term = Column(String, nullable=False)
    mnemonic_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
