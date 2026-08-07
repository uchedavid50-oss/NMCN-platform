import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rationale import WhyOthersWrongMixin


class CBTExamStartRequest(BaseModel):
    question_count: int = Field(default=250, ge=10, le=300)
    duration_minutes: int = Field(default=240, ge=30, le=300)


class CBTExamOption(BaseModel):
    id: uuid.UUID
    text: str

    class Config:
        from_attributes = True


class CBTExamQuestion(BaseModel):
    id: uuid.UUID
    stem: str
    options: List[CBTExamOption]

    class Config:
        from_attributes = True


class CBTExamStartResponse(BaseModel):
    session_id: uuid.UUID
    question_count: int
    time_limit_minutes: int
    started_at: datetime
    expires_at: datetime
    questions: List[CBTExamQuestion]


class CBTExamAnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class CBTExamAnswerAck(BaseModel):
    received: bool
    message: str


class CBTExamBreakdownItem(WhyOthersWrongMixin, BaseModel):
    question_id: uuid.UUID
    stem: str
    subject_name: str
    your_answer_text: Optional[str]
    correct_option_text: str
    is_correct: bool
    explanation: str
    # All 4 option texts in stored order -- lets the frontend map
    # why_others_wrong's letter keys (A = 1st option, ...) back to text.
    option_texts: List[str] = []
    clinical_tip: Optional[str] = None
    exam_specific_tip: Optional[str] = None
    cognitive_level: Optional[str] = None
    exam_type: Optional[str] = None


class CBTExamSubmitResponse(BaseModel):
    session_id: uuid.UUID
    total_questions: int
    correct_answers: int
    score_percentage: float
    started_at: datetime
    finished_at: datetime
    breakdown: List[CBTExamBreakdownItem]


class CBTExamStatus(BaseModel):
    session_id: uuid.UUID
    started_at: datetime
    expires_at: datetime
    finished_at: Optional[datetime]
    time_remaining_seconds: int
    is_expired: bool
