import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.option import Option
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionOut, QuestionUpdate

router = APIRouter(prefix="/questions", tags=["questions"])

# Every endpoint here requires admin — even reads — because QuestionOut includes
# is_correct and explanation. A student hitting this directly would see the
# answer key, bypassing practice/mock mode entirely. Students only ever see
# questions through /practice and /mock, which use answer-key-free schemas.


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    question = Question(
        topic_id=payload.topic_id,
        stem=payload.stem,
        difficulty=payload.difficulty,
        explanation=payload.explanation,
    )
    question.options = [Option(text=o.text, is_correct=o.is_correct) for o in payload.options]
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("", response_model=List[QuestionOut])
def list_questions(
    topic_id: Optional[uuid.UUID] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(Question)
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    return query.all()


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    question.topic_id = payload.topic_id
    question.stem = payload.stem
    question.difficulty = payload.difficulty
    question.explanation = payload.explanation

    # Full replace of options, per QuestionUpdate's contract.
    for old_option in list(question.options):
        db.delete(old_option)
    question.options = [Option(text=o.text, is_correct=o.is_correct) for o in payload.options]

    db.commit()
    db.refresh(question)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)  # cascades to options
    db.commit()
    return None
