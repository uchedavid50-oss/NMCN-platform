import uuid

from pydantic import BaseModel


class TopicCreate(BaseModel):
    subject_id: uuid.UUID
    name: str


class TopicUpdate(BaseModel):
    name: str


class TopicOut(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    name: str

    class Config:
        from_attributes = True
