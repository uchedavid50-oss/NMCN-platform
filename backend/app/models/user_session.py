import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.time import utcnow
from app.db.session import Base


class UserSession(Base):
    """One row per logged-in device. The row's id doubles as the JWT's jti
    claim -- a token only authenticates a request as long as its matching
    session row still exists, which is what lets logging out a specific
    device from Settings take effect immediately rather than waiting for
    the token to expire on its own. Logging out deletes the row outright
    (no revoked_at soft-delete) -- row exists means session is active."""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_label = Column(String, nullable=False)  # e.g. "Chrome on Windows 10", parsed from user_agent
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    last_active_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # mirrors the JWT's own exp

    user = relationship("User")
