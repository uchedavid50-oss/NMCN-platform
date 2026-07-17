import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


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


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_option_id: uuid.UUID
    explanation: str


class AttemptSummary(BaseModel):
    attempt_id: uuid.UUID
    total_questions: int
    correct_answers: int
    score_percentage: float
    started_at: datetime
    finished_at: Optional[datetime]
