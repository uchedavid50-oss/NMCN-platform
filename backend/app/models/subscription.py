import uuid
from app.core.time import utcnow

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(String, nullable=False, default="premium_monthly")
    status = Column(String, nullable=False, default="pending")  # pending | active | failed | expired
    provider = Column(String, nullable=False, default="paystack")
    reference = Column(String, unique=True, nullable=False, index=True)
    amount_kobo = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="NGN")
    created_at = Column(DateTime, default=utcnow)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
