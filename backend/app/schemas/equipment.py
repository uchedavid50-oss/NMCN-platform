import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EquipmentOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    youtube_url: Optional[str] = None
    pdf_filename: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class SetEquipmentRequest(BaseModel):
    title: str
    description: str
    youtube_url: Optional[str] = None
