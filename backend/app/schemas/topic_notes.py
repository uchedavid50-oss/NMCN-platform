import uuid
from datetime import datetime
from pydantic import BaseModel


class TopicNoteOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    content: str
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateNoteRequest(BaseModel):
    topic_id: uuid.UUID