import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AdminDocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    document_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratePendingRequest(BaseModel):
    document_id: uuid.UUID
    topic_id: uuid.UUID
    count: int = Field(default=10, ge=1, le=30)


class PendingOptionOut(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class PendingQuestionOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    stem: str
    difficulty: str
    explanation: str
    status: str
    created_at: datetime
    options: List[PendingOptionOut]

    class Config:
        from_attributes = True


class BulkImportResult(BaseModel):
    created_count: int
    skipped_rows: List[str]
