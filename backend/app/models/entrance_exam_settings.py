from sqlalchemy import Column, Integer

from app.db.session import Base


class EntranceExamSettings(Base):
    """Single-row table (id is always 1) holding admin-configurable knobs for
    the entrance exam question bank -- currently just the free-tier per-subject
    question cap. A dedicated table rather than a generic key/value settings
    table since this is the only such setting the app has so far."""
    __tablename__ = "entrance_exam_settings"

    id = Column(Integer, primary_key=True)
    free_questions_per_subject = Column(Integer, nullable=False, default=2)
