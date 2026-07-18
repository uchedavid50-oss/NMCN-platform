import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class SpeedRoundOption(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class SpeedRoundQuestion(BaseModel):
    id: uuid.UUID
    stem: str
    options: List[SpeedRoundOption]

    class Config:
        from_attributes = True


class SpeedRoundSubmitRequest(BaseModel):
    topic_id: Optional[uuid.UUID] = None
    total_questions: int = Field(ge=1)
    correct_answers: int = Field(ge=0)


class SpeedRoundSubmitResponse(BaseModel):
    score_percentage: float
    current_streak: int
    played_today: bool


class StreakResponse(BaseModel):
    current_streak: int
    played_today: bool


class LeaderboardOptInRequest(BaseModel):
    opt_in: bool
    display_name: Optional[str] = Field(default=None, max_length=30)


class LeaderboardEntry(BaseModel):
    display_name: str
    current_streak: int
    best_score_percentage: float
