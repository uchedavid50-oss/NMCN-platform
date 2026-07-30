import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

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
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateEntranceExamRequest(BaseModel):
    subject: EntranceExamSubject
