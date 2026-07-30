import uuid
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.time import utcnow
from app.db.session import Base


class AIProviderAttempt(Base):
    """Append-only log of every attempt the entrance-exam AI provider
    router makes (backend/app/services/ai_router.py) -- one row per
    provider tried per generation call, success or failure. Drives the
    admin panel's per-provider health indicator and "last used" display."""
    __tablename__ = "ai_provider_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
