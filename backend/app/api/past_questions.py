from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.question import Question
from app.models.speed_round import SpeedRoundResult
from app.models.user import User
from app.schemas.games import SpeedRoundQuestion, SpeedRoundSubmitRequest, SpeedRoundSubmitResponse
from app.services.streaks import compute_streak

router = APIRouter(prefix="/past-questions", tags=["past-questions"])


@router.get("/count")
def get_past_questions_count(db: Session = Depends(get_db)):
    count = db.query(Question).filter(Question.source == "past_questions").count()
    return {"count": count}


@router.get("/practice", response_model=list[SpeedRoundQuestion])
def start_past_questions_practice(
    count: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Same design reasoning as flashcards and speed round: this is a review
    tool for material approved from real past-exam questions, not the
    formal certification-relevant assessment engine, so showing the answer
    immediately (via SpeedRoundQuestion, which includes is_correct) is
    intentional, not a leak."""
    questions = (
        db.query(Question)
        .options(joinedload(Question.options))
        .filter(Question.source == "past_questions")
        .order_by(func.random())
        .limit(count)
        .all()
    )
    if not questions:
        raise HTTPException(
            status_code=400,
            detail="No past-questions-derived content is available yet. Ask your admin to generate and approve some first.",
        )
    return questions


@router.post("/complete", response_model=SpeedRoundSubmitResponse)
def complete_past_questions_practice(
    payload: SpeedRoundSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reuses the SpeedRoundResult model for logging -- same shape (total
    questions, correct answers, score, timestamp), same contribution to the
    daily streak, just a different practice mode feeding it."""
    if payload.correct_answers > payload.total_questions:
        raise HTTPException(status_code=400, detail="correct_answers can't exceed total_questions")

    score_percentage = round((payload.correct_answers / payload.total_questions) * 100, 2)
    result = SpeedRoundResult(
        user_id=current_user.id,
        topic_id=None,
        total_questions=payload.total_questions,
        correct_answers=payload.correct_answers,
        score_percentage=score_percentage,
    )
    db.add(result)
    db.commit()

    streak, played_today = compute_streak(db, current_user.id)
    return SpeedRoundSubmitResponse(
        score_percentage=score_percentage,
        current_streak=streak,
        played_today=played_today,
    )
