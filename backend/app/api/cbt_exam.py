import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.time import utcnow
from app.db.session import get_db
from app.models.cbt_exam import CBTExamSession
from app.models.cbt_exam_answer import CBTExamAnswer
from app.models.question import Question
from app.models.user import User
from app.schemas.cbt_exam import (
    CBTExamAnswerAck,
    CBTExamAnswerRequest,
    CBTExamBreakdownItem,
    CBTExamStartRequest,
    CBTExamStartResponse,
    CBTExamStatus,
    CBTExamSubmitResponse,
)
from app.services.cbt_cleanup import finalize_expired_cbt_sessions

router = APIRouter(prefix="/cbt-exam", tags=["cbt-exam"])

# The flagship "real exam simulation" feature — free tier gets one attempt to
# see what it's like, same pattern as the free-tier mock exam limit (Module 6).
FREE_TIER_CBT_EXAM_LIMIT = 1


@router.post("/start", response_model=CBTExamStartResponse, status_code=status.HTTP_201_CREATED)
def start_cbt_exam(
    payload: CBTExamStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.subscription_status != "active":
        finalize_expired_cbt_sessions(db, current_user.id)
        existing_count = (
            db.query(CBTExamSession).filter(CBTExamSession.user_id == current_user.id).count()
        )
        if existing_count >= FREE_TIER_CBT_EXAM_LIMIT:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Free tier is limited to {FREE_TIER_CBT_EXAM_LIMIT} full CBT exam simulation. "
                    "Subscribe via POST /payments/initialize to unlock unlimited full exam simulations."
                ),
            )

    questions = (
        db.query(Question)
        .options(joinedload(Question.options))
        .order_by(func.random())
        .limit(payload.question_count)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=400, detail="No questions are available yet for a CBT exam.")

    now = utcnow()
    expires_at = now + timedelta(minutes=payload.duration_minutes)

    session = CBTExamSession(
        user_id=current_user.id,
        question_ids=[q.id for q in questions],
        question_count=len(questions),
        time_limit_minutes=payload.duration_minutes,
        started_at=now,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return CBTExamStartResponse(
        session_id=session.id,
        question_count=len(questions),
        time_limit_minutes=payload.duration_minutes,
        started_at=now,
        expires_at=expires_at,
        questions=questions,
    )


def _get_owned_session(session_id: uuid.UUID, db: Session, current_user: User) -> CBTExamSession:
    finalize_expired_cbt_sessions(db, current_user.id)
    session = db.query(CBTExamSession).filter(CBTExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="CBT exam session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This exam session does not belong to you")
    return session


@router.post("/{session_id}/answer", response_model=CBTExamAnswerAck)
def submit_cbt_answer(
    session_id: uuid.UUID,
    payload: CBTExamAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, db, current_user)

    if session.finished_at is not None:
        raise HTTPException(status_code=400, detail="This exam has already been submitted")
    if utcnow() > session.expires_at:
        raise HTTPException(status_code=400, detail="Time limit exceeded. Please submit your exam.")
    if payload.question_id not in session.question_ids:
        raise HTTPException(status_code=400, detail="This question is not part of this exam session")

    question = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.id == payload.question_id)
        .first()
    )
    selected_option = next((o for o in question.options if o.id == payload.selected_option_id), None)
    if not selected_option:
        raise HTTPException(status_code=400, detail="That option does not belong to this question")

    existing = (
        db.query(CBTExamAnswer)
        .filter(CBTExamAnswer.session_id == session_id, CBTExamAnswer.question_id == payload.question_id)
        .first()
    )
    if existing:
        existing.selected_option_id = selected_option.id
        existing.is_correct = selected_option.is_correct
        db.commit()
        return CBTExamAnswerAck(received=True, message="Answer updated")

    db.add(
        CBTExamAnswer(
            session_id=session_id,
            question_id=question.id,
            selected_option_id=selected_option.id,
            is_correct=selected_option.is_correct,
        )
    )
    db.commit()
    return CBTExamAnswerAck(received=True, message="Answer recorded")


@router.post("/{session_id}/submit", response_model=CBTExamSubmitResponse)
def submit_cbt_exam(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, db, current_user)
    if session.finished_at is not None:
        raise HTTPException(status_code=400, detail="This exam has already been submitted")

    questions = (
        db.query(Question)
        .options(joinedload(Question.options), joinedload(Question.topic))
        .filter(Question.id.in_(session.question_ids))
        .all()
    )
    answers_by_question = {
        a.question_id: a
        for a in db.query(CBTExamAnswer).filter(CBTExamAnswer.session_id == session_id).all()
    }

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
            CBTExamBreakdownItem(
                question_id=question.id,
                stem=question.stem,
                subject_name=question.topic.subject.name if question.topic and question.topic.subject else "—",
                your_answer_text=selected_option.text if selected_option else None,
                correct_option_text=correct_option.text,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    total_questions = len(questions)
    score_percentage = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0

    session.finished_at = utcnow()
    session.score_percentage = score_percentage
    db.commit()
    db.refresh(session)

    return CBTExamSubmitResponse(
        session_id=session.id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=score_percentage,
        started_at=session.started_at,
        finished_at=session.finished_at,
        breakdown=breakdown,
    )


@router.get("/{session_id}", response_model=CBTExamStatus)
def get_cbt_exam_status(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, db, current_user)
    now = utcnow()
    remaining = (session.expires_at - now).total_seconds()

    return CBTExamStatus(
        session_id=session.id,
        started_at=session.started_at,
        expires_at=session.expires_at,
        finished_at=session.finished_at,
        time_remaining_seconds=max(0, int(remaining)),
        is_expired=remaining <= 0,
    )
