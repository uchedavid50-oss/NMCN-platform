import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rationale import WhyOthersWrongMixin


class AdminDocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    document_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratePendingRequest(BaseModel):
    document_id: Optional[uuid.UUID] = None
    topic_id: uuid.UUID
    count: int = Field(default=10, ge=1, le=30)
    extraction_mode: str = Field(default="ai_generate")  # "ai_generate" | "verbatim"
class PendingOptionOut(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class PendingQuestionOut(WhyOthersWrongMixin, BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    stem: str
    difficulty: str
    explanation: str
    clinical_tip: Optional[str] = None
    exam_specific_tip: Optional[str] = None
    cognitive_level: Optional[str] = None
    # Derived from topic.subject.exam_type at request time, not a stored column --
    # lets the frontend label exam_specific_tip "NMCN Tip" vs "NCLEX Tip".
    exam_type: Optional[str] = None
    status: str
    created_at: datetime
    options: List[PendingOptionOut]

    class Config:
        from_attributes = True


class BulkImportResult(BaseModel):
    created_count: int
    skipped_rows: List[str]
