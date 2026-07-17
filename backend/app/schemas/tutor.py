import uuid

from pydantic import BaseModel, Field


class TutorAskRequest(BaseModel):
    question_id: uuid.UUID
    message: str = Field(min_length=1, max_length=500)


class TutorAskResponse(BaseModel):
    reply: str


class StudyPlanResponse(BaseModel):
    has_weak_topics: bool
    weak_topic_names: list[str]
    plan: str
