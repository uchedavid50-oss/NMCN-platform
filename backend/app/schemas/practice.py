import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.rationale import WhyOthersWrongMixin


class PracticeStartRequest(BaseModel):
    topic_id: uuid.UUID


class OptionForPractice(BaseModel):
    """Deliberately excludes is_correct — a student practicing shouldn't see the
    answer key until after they submit."""
    id: uuid.UUID
    text: str

    class Config:
        from_attributes = True


class QuestionForPractice(BaseModel):
    """Deliberately excludes explanation — same reasoning as above."""
    id: uuid.UUID
    stem: str
    difficulty: str
    options: List[OptionForPractice]

    class Config:
        from_attributes = True


class PracticeStartResponse(BaseModel):
    attempt_id: uuid.UUID
    topic_id: uuid.UUID
    questions: List[QuestionForPractice]


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class AnswerResponse(WhyOthersWrongMixin, BaseModel):
    is_correct: bool
    correct_option_id: uuid.UUID
    explanation: str
    clinical_tip: Optional[str] = None
    exam_specific_tip: Optional[str] = None
    cognitive_level: Optional[str] = None
    # Derived from topic.subject.exam_type -- lets the frontend label
    # exam_specific_tip "NMCN Tip" vs "NCLEX Tip".
    exam_type: Optional[str] = None


class AttemptSummary(BaseModel):
    attempt_id: uuid.UUID
    total_questions: int
    correct_answers: int
    score_percentage: float
    started_at: datetime
    finished_at: Optional[datetime]
