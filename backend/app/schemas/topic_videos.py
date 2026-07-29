import uuid
from datetime import datetime
from pydantic import BaseModel


class TopicVideoOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    youtube_url: str
    updated_at: datetime

    class Config:
        from_attributes = True


class SetTopicVideoRequest(BaseModel):
    youtube_url: str
