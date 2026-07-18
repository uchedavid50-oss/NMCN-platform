import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class NoteOut(BaseModel):
    id: uuid.UUID
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateQuestionsRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=10)


class GeneratedOptionOut(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class GeneratedQuestionOut(BaseModel):
    id: uuid.UUID
    stem: str
    difficulty: str
    explanation: str
    options: List[GeneratedOptionOut]

    class Config:
        from_attributes = True
