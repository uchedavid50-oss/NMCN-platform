import uuid
from datetime import timedelta

from app.core.time import utcnow

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.services.mock_cleanup import finalize_expired_mock_attempts
from app.schemas.mock import (
    MockAnswerAck,
    MockAnswerRequest,
    MockStartRequest,
    MockStartResponse,
    MockStatus,
    MockSubmitResponse,
    QuestionBreakdown,
)

router = APIRouter(prefix="/mock", tags=["mock-exam"])

# Free-tier users get a limited number of mock exams total; an active subscription removes the cap.
FREE_TIER_MOCK_LIMIT = 3


@router.post("/start", response_model=MockStartResponse, status_code=status.HTTP_201_CREATED)
def start_mock_exam(
    payload: MockStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.subscription_status != "active":
        finalize_expired_mock_attempts(db, current_user.id)
        existing_mock_count = (
            db.query(Attempt)
            .filter(Attempt.user_id == current_user.id, Attempt.mode == "mock")
            .count()
        )
        if existing_mock_count >= FREE_TIER_MOCK_LIMIT:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Free tier is limited to {FREE_TIER_MOCK_LIMIT} mock exams. "
                    "Subscribe via POST /payments/initialize to unlock unlimited mock exams."
                ),
            )

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

    now = utcnow()
    expires_at = now + timedelta(minutes=payload.duration_minutes)

    attempt = Attempt(
        user_id=current_user.id,
        topic_id=payload.topic_id,
        mode="mock",
        started_at=now,
        time_limit_minutes=payload.duration_minutes,
        expires_at=expires_at,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return MockStartResponse(
        attempt_id=attempt.id,
        topic_id=topic.id,
        time_limit_minutes=payload.duration_minutes,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        questions=questions,
    )


def _get_owned_mock_attempt(attempt_id: uuid.UUID, db: Session, current_user: User) -> Attempt:
    finalize_expired_mock_attempts(db, current_user.id)
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id, Attempt.mode == "mock").first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Mock exam attempt not found")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This attempt does not belong to you")
    return attempt


@router.post("/{attempt_id}/answer", response_model=MockAnswerAck)
def submit_mock_answer(
    attempt_id: uuid.UUID,
    payload: MockAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_owned_mock_attempt(attempt_id, db, current_user)

    if attempt.finished_at is not None:
        raise HTTPException(status_code=400, detail="This exam has already been submitted")
    if utcnow() > attempt.expires_at:
        raise HTTPException(status_code=400, detail="Time limit exceeded. Please submit your exam.")

    question = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.id == payload.question_id, Question.topic_id == attempt.topic_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found for this exam's topic")

    selected_option = next((o for o in question.options if o.id == payload.selected_option_id), None)
    if not selected_option:
        raise HTTPException(status_code=400, detail="That option does not belong to this question")

    existing = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id, AttemptAnswer.question_id == payload.question_id)
        .first()
    )
    if existing:
        # Unlike practice mode, mock exams allow changing your answer before submitting —
        # you can revisit and change your mind, same as a real CBT exam interface.
        existing.selected_option_id = selected_option.id
        existing.is_correct = selected_option.is_correct
        db.commit()
        return MockAnswerAck(received=True, message="Answer updated")

    answer = AttemptAnswer(
        attempt_id=attempt_id,
        question_id=question.id,
        selected_option_id=selected_option.id,
        is_correct=selected_option.is_correct,
    )
    db.add(answer)
    db.commit()

    return MockAnswerAck(received=True, message="Answer recorded")


@router.post("/{attempt_id}/submit", response_model=MockSubmitResponse)
def submit_mock_exam(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_owned_mock_attempt(attempt_id, db, current_user)
    if attempt.finished_at is not None:
        raise HTTPException(status_code=400, detail="This exam has already been submitted")

    questions = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.topic_id == attempt.topic_id)
        .all()
    )
    answers_by_question = {a.question_id: a for a in attempt.answers}

    breakdown = []
    correct_count = 0
    for question in questions:
        correct_option = next(o for o in question.options if o.is_correct)
        answer = answers_by_question.get(question.id)
        selected_option = None
        if answer:
            selected_option = next((o for o in question.options if o.id == answer.selected_option_id), None)
        is_correct = bool(answer and answer.is_correct)
        if is_correct:
            correct_count += 1

        breakdown.append(
            QuestionBreakdown(
                question_id=question.id,
                stem=question.stem,
                your_answer_id=selected_option.id if selected_option else None,
                your_answer_text=selected_option.text if selected_option else None,
                correct_option_id=correct_option.id,
                correct_option_text=correct_option.text,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    total_questions = len(questions)
    score_percentage = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0

    attempt.finished_at = utcnow()
    attempt.score_percentage = score_percentage
    db.commit()
    db.refresh(attempt)

    return MockSubmitResponse(
        attempt_id=attempt.id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=score_percentage,
        started_at=attempt.started_at,
        finished_at=attempt.finished_at,
        time_limit_minutes=attempt.time_limit_minutes,
        breakdown=breakdown,
    )


@router.get("/{attempt_id}", response_model=MockStatus)
def get_mock_status(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_owned_mock_attempt(attempt_id, db, current_user)

    now = utcnow()
    remaining = (attempt.expires_at - now).total_seconds()
    time_remaining_seconds = max(0, int(remaining))

    return MockStatus(
        attempt_id=attempt.id,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        finished_at=attempt.finished_at,
        time_remaining_seconds=time_remaining_seconds,
        is_expired=remaining <= 0,
    )
