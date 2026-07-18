import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ClinicalCaseGenerateRequest(BaseModel):
    subject_id: Optional[uuid.UUID] = None


class ClinicalCaseOptionOut(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool
    rationale: str

    class Config:
        from_attributes = True


class ClinicalCaseDecisionPointOut(BaseModel):
    id: uuid.UUID
    order_index: int
    question: str
    options: List[ClinicalCaseOptionOut]

    class Config:
        from_attributes = True


class ClinicalCaseOut(BaseModel):
    id: uuid.UUID
    subject_context: Optional[str]
    scenario: str
    created_at: datetime
    decision_points: List[ClinicalCaseDecisionPointOut]

    class Config:
        from_attributes = True


class ClinicalCaseSummary(BaseModel):
    """Lightweight version for list views — no decision points."""

    id: uuid.UUID
    subject_context: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ClinicalCaseCompleteRequest(BaseModel):
    total_decisions: int = Field(ge=1)
    correct_decisions: int = Field(ge=0)


class ClinicalCaseCompleteResponse(BaseModel):
    score_percentage: float
    current_streak: int
