import uuid
from datetime import datetime

from pydantic import BaseModel


class TextbookFolderCreate(BaseModel):
    name: str


class TextbookFolderOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TextbookOut(BaseModel):
    id: uuid.UUID
    folder_id: uuid.UUID
    title: str
    filename: str
    content_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True
