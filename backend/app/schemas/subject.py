import uuid

from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str


class SubjectUpdate(BaseModel):
    name: str


class SubjectOut(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True
