import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DictionarySearchRequest(BaseModel):
    term: str = Field(min_length=1, max_length=100)


class DictionaryEntryOut(BaseModel):
    id: uuid.UUID
    term: str
    definition: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DictionaryVerifyRequest(BaseModel):
    definition: Optional[str] = None
