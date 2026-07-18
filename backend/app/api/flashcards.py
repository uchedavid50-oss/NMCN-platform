import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.schemas.flashcard import Flashcard

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("", response_model=List[Flashcard])
def get_flashcards(
    topic_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unlike /questions (admin-only, Module 8), this deliberately shows the
    answer to any logged-in student — that's the entire point of a flashcard,
    not a leak. Practice/mock mode integrity depends on hiding answers until
    the student commits to a choice; flashcards are an explicit "just show me
    the answer" review tool, a different use case with a different contract."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    questions = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.topic_id == topic_id)
        .all()
    )

    cards = []
    for question in questions:
        correct_option = next((o for o in question.options if o.is_correct), None)
        answer_text = correct_option.text if correct_option else "—"
        cards.append(
            Flashcard(
                question_id=question.id,
                front=question.stem,
                back=f"{answer_text}\n\n{question.explanation}",
            )
        )
    return cards
