import uuid
from typing import List

from pydantic import BaseModel, field_validator, model_validator


class OptionCreate(BaseModel):
    text: str
    is_correct: bool = False


class OptionOut(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    topic_id: uuid.UUID
    stem: str
    difficulty: str = "medium"
    explanation: str
    options: List[OptionCreate]

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        if v not in ("easy", "medium", "hard"):
            raise ValueError("difficulty must be one of: easy, medium, hard")
        return v

    @model_validator(mode="after")
    def validate_options(self):
        if len(self.options) < 2:
            raise ValueError("a question must have at least 2 answer options")
        correct_count = sum(1 for o in self.options if o.is_correct)
        if correct_count != 1:
            raise ValueError("a question must have exactly one correct option")
        return self


class QuestionUpdate(QuestionCreate):
    """Full replace: updating a question replaces its options entirely."""
    pass


class QuestionOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    stem: str
    difficulty: str
    explanation: str
    options: List[OptionOut]

    class Config:
        from_attributes = True
