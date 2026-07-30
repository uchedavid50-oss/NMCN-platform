import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

ENTRANCE_EXAM_SUBJECTS = ("Biology", "Chemistry", "Current Affairs", "English", "Mathematics", "Physics")

EntranceExamSubject = Literal[
    "Biology", "Chemistry", "Current Affairs", "English", "Mathematics", "Physics"
]


class EntranceExamQuestionOut(BaseModel):
    id: uuid.UUID
    subject: str
    question_type: str
    question_text: str
    model_answer: str
    explanation: str
    provider: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateEntranceExamRequest(BaseModel):
    subject: EntranceExamSubject


class ProviderStatusEntry(BaseModel):
    name: str
    configured: bool
    status: Literal["healthy", "failing", "unknown"]
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None


class LastUsedProvider(BaseModel):
    provider: str
    at: datetime


class SubjectCount(BaseModel):
    subject: str
    count: int


class ProviderStatusOut(BaseModel):
    providers: list[ProviderStatusEntry]
    last_used: Optional[LastUsedProvider] = None
    question_counts: list[SubjectCount]


class ProviderRunResultOut(BaseModel):
    provider: str
    status: Literal["success", "failed", "skipped_no_key", "skipped_daily_limit"]
    questions_generated: int
    elapsed_seconds: float
    error: Optional[str] = None


class GenerateBatchResult(BaseModel):
    results: list[ProviderRunResultOut]
    saved_questions: list[EntranceExamQuestionOut]
    total_saved: int
    total_generated_before_dedup: int
