import uuid
from app.core.time import utcnow

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")  # student | admin
    subscription_status = Column(String, nullable=False, default="free")  # free | active | expired
    created_at = Column(DateTime, default=utcnow)
