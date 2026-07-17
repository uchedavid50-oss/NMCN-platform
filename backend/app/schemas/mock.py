import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.practice import QuestionForPractice


class MockStartRequest(BaseModel):
    topic_id: uuid.UUID
    duration_minutes: int = Field(default=30, ge=1, le=180)


class MockStartResponse(BaseModel):
    attempt_id: uuid.UUID
    topic_id: uuid.UUID
    time_limit_minutes: int
    started_at: datetime
    expires_at: datetime
    questions: List[QuestionForPractice]


class MockAnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class MockAnswerAck(BaseModel):
    """Deliberately reveals nothing about correctness — that's the whole point
    of a mock exam versus practice mode."""
    received: bool
    message: str


class QuestionBreakdown(BaseModel):
    question_id: uuid.UUID
    stem: str
    your_answer_id: Optional[uuid.UUID]
    your_answer_text: Optional[str]
    correct_option_id: uuid.UUID
    correct_option_text: str
    is_correct: bool
    explanation: str


class MockSubmitResponse(BaseModel):
    attempt_id: uuid.UUID
    total_questions: int
    correct_answers: int
    score_percentage: float
    started_at: datetime
    finished_at: datetime
    time_limit_minutes: int
    breakdown: List[QuestionBreakdown]


class MockStatus(BaseModel):
    attempt_id: uuid.UUID
    started_at: datetime
    expires_at: datetime
    finished_at: Optional[datetime]
    time_remaining_seconds: int
    is_expired: bool
