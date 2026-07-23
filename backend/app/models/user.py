import uuid
from app.core.time import utcnow

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")  # student | admin
    subscription_status = Column(String, nullable=False, default="free")  # free | active | expired
    leaderboard_opt_in = Column(Boolean, nullable=False, default=False)
    display_name = Column(String, nullable=True)
    # Brute-force login protection: after MAX_FAILED_LOGIN_ATTEMPTS (see auth.py),
    # locked_until is set and login is rejected until that time passes.
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
