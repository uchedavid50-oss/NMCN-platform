import uuid

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.time import utcnow
from app.db.session import Base

# Standard 5-point grading scale used across Nigerian universities/nursing schools.
GRADE_POINTS = {"A": 5.0, "B": 4.0, "C": 3.0, "D": 2.0, "E": 1.0, "F": 0.0}


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    semester = Column(String, nullable=False)  # e.g. "300 Level, First Semester"
    course_name = Column(String, nullable=False)
    credit_units = Column(Integer, nullable=False)
    grade = Column(String, nullable=False)  # A/B/C/D/E/F
    created_at = Column(DateTime, default=utcnow)
