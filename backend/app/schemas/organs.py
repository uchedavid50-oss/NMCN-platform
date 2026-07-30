import uuid
from datetime import datetime
from pydantic import BaseModel


class OrganOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str

    class Config:
        from_attributes = True


class OrganVideoOut(BaseModel):
    id: uuid.UUID
    organ_id: uuid.UUID
    youtube_url: str
    updated_at: datetime

    class Config:
        from_attributes = True


class SetOrganVideoRequest(BaseModel):
    youtube_url: str
