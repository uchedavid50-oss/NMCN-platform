import uuid
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator

from app.schemas.rationale import WhyOthersWrongMixin


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


class QuestionOut(WhyOthersWrongMixin, BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    stem: str
    difficulty: str
    explanation: str
    clinical_tip: Optional[str] = None
    exam_specific_tip: Optional[str] = None
    cognitive_level: Optional[str] = None
    # Derived from topic.subject.exam_type at request time, not a stored column.
    exam_type: Optional[str] = None
    options: List[OptionOut]

    class Config:
        from_attributes = True
