import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MnemonicGenerateRequest(BaseModel):
    term: str = Field(min_length=1, max_length=200)


class MnemonicOut(BaseModel):
    id: uuid.UUID
    term: str
    mnemonic_text: str
    created_at: datetime

    class Config:
        from_attributes = True
