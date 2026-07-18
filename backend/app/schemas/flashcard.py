import uuid

from pydantic import BaseModel


class Flashcard(BaseModel):
    question_id: uuid.UUID
    front: str  # the question stem
    back: str  # correct answer + explanation, combined for quick review
