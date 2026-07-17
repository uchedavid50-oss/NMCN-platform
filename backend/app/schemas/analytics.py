import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_attempts: int
    completed_attempts: int
    practice_attempts: int
    mock_attempts: int
    total_questions_answered: int
    total_correct: int
    overall_accuracy_percentage: float


class TopicPerformance(BaseModel):
    topic_id: uuid.UUID
    topic_name: str
    subject_name: str
    total_answered: int
    correct_answered: int
    accuracy_percentage: float
    last_attempted_at: Optional[datetime]


class AttemptHistoryItem(BaseModel):
    attempt_id: uuid.UUID
    mode: str
    topic_name: str
    subject_name: str
    score_percentage: Optional[float]
    started_at: datetime
    finished_at: Optional[datetime]


class AttemptHistory(BaseModel):
    total: int
    items: List[AttemptHistoryItem]
