import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.option import Option
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.schemas.practice import (
    AnswerRequest,
    AnswerResponse,
    AttemptSummary,
    PracticeStartRequest,
    PracticeStartResponse,
)

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/start", response_model=PracticeStartResponse, status_code=status.HTTP_201_CREATED)
def start_practice(
    payload: PracticeStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    questions = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.topic_id == payload.topic_id)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=400, detail="This topic has no questions yet")

    attempt = Attempt(user_id=current_user.id, topic_id=payload.topic_id, mode="practice")
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return PracticeStartResponse(
        attempt_id=attempt.id,
        topic_id=topic.id,
        questions=questions,
    )


@router.post("/{attempt_id}/answer", response_model=AnswerResponse)
def submit_answer(
    attempt_id: uuid.UUID,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This attempt does not belong to you")
    if attempt.finished_at is not None:
        raise HTTPException(status_code=400, detail="This attempt has already been finished")

    question = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.id == payload.question_id, Question.topic_id == attempt.topic_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found for this attempt's topic")

    already_answered = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id, AttemptAnswer.question_id == payload.question_id)
        .first()
    )
    if already_answered:
        raise HTTPException(status_code=400, detail="This question has already been answered in this attempt")

    selected_option = next((o for o in question.options if o.id == payload.selected_option_id), None)
    if not selected_option:
        raise HTTPException(status_code=400, detail="That option does not belong to this question")

    correct_option = next(o for o in question.options if o.is_correct)

    answer = AttemptAnswer(
        attempt_id=attempt_id,
        question_id=question.id,
        selected_option_id=selected_option.id,
        is_correct=selected_option.is_correct,
    )
    db.add(answer)
    db.commit()

    return AnswerResponse(
        is_correct=selected_option.is_correct,
        correct_option_id=correct_option.id,
        explanation=question.explanation,
    )


@router.post("/{attempt_id}/finish", response_model=AttemptSummary)
def finish_practice(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.time import utcnow

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This attempt does not belong to you")
    if attempt.finished_at is not None:
        raise HTTPException(status_code=400, detail="This attempt has already been finished")

    total_questions = db.query(Question).filter(Question.topic_id == attempt.topic_id).count()
    correct_answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id, AttemptAnswer.is_correct == True)  # noqa: E712
        .count()
    )
    score_percentage = round((correct_answers / total_questions) * 100, 2) if total_questions else 0.0

    attempt.finished_at = utcnow()
    attempt.score_percentage = score_percentage
    db.commit()
    db.refresh(attempt)

    return AttemptSummary(
        attempt_id=attempt.id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        score_percentage=score_percentage,
        started_at=attempt.started_at,
        finished_at=attempt.finished_at,
    )


@router.get("/{attempt_id}", response_model=AttemptSummary)
def get_attempt_status(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This attempt does not belong to you")

    total_questions = db.query(Question).filter(Question.topic_id == attempt.topic_id).count()
    correct_answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id, AttemptAnswer.is_correct == True)  # noqa: E712
        .count()
    )

    return AttemptSummary(
        attempt_id=attempt.id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        score_percentage=attempt.score_percentage or 0.0,
        started_at=attempt.started_at,
        finished_at=attempt.finished_at,
    )
