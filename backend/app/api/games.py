import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.question import Question
from app.models.speed_round import SpeedRoundResult
from app.models.topic import Topic
from app.models.user import User
from app.schemas.games import (
    LeaderboardEntry,
    LeaderboardOptInRequest,
    SpeedRoundQuestion,
    SpeedRoundSubmitRequest,
    SpeedRoundSubmitResponse,
    StreakResponse,
)
from app.services.streaks import compute_streak

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/speed-round/start", response_model=list[SpeedRoundQuestion])
def start_speed_round(
    topic_id: Optional[uuid.UUID] = Query(default=None),
    count: int = Query(default=10, ge=1, le=25),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deliberately includes is_correct in the response, unlike /practice and
    /mock — this is a casual arcade-style game (Module 24), not a scored,
    certification-relevant assessment, so instant per-question feedback is
    the intended mechanic rather than something to guard against. Same
    reasoning as flashcards (Module 20): open to any student, answers visible
    by design."""
    query = db.query(Question).options(joinedload(Question.options))
    if topic_id:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        query = query.filter(Question.topic_id == topic_id)

    questions = query.order_by(func.random()).limit(count).all()
    if not questions:
        raise HTTPException(status_code=400, detail="No questions available for a speed round yet.")

    return questions


@router.post("/speed-round/submit", response_model=SpeedRoundSubmitResponse)
def submit_speed_round(
    payload: SpeedRoundSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.correct_answers > payload.total_questions:
        raise HTTPException(status_code=400, detail="correct_answers can't exceed total_questions")

    score_percentage = round((payload.correct_answers / payload.total_questions) * 100, 2)

    result = SpeedRoundResult(
        user_id=current_user.id,
        topic_id=payload.topic_id,
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


@router.get("/streak", response_model=StreakResponse)
def get_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    streak, played_today = compute_streak(db, current_user.id)
    return StreakResponse(current_streak=streak, played_today=played_today)


@router.patch("/leaderboard/opt-in", response_model=StreakResponse)
def set_leaderboard_opt_in(
    payload: LeaderboardOptInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opt-in only, by design — a student's streak and activity are never
    shown to other students unless they explicitly choose to be listed, and
    even then only under a display name they pick, not their real email."""
    current_user.leaderboard_opt_in = payload.opt_in
    if payload.display_name:
        current_user.display_name = payload.display_name
    db.commit()

    streak, played_today = compute_streak(db, current_user.id)
    return StreakResponse(current_streak=streak, played_today=played_today)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opted_in_users = db.query(User).filter(User.leaderboard_opt_in.is_(True)).all()

    entries = []
    for user in opted_in_users:
        streak, _ = compute_streak(db, user.id)
        best_score = (
            db.query(func.max(SpeedRoundResult.score_percentage))
            .filter(SpeedRoundResult.user_id == user.id)
            .scalar()
        )
        entries.append(
            LeaderboardEntry(
                display_name=user.display_name or "Anonymous student",
                current_streak=streak,
                best_score_percentage=best_score or 0.0,
            )
        )

    entries.sort(key=lambda e: (-e.current_streak, -e.best_score_percentage))
    return entries[:20]
