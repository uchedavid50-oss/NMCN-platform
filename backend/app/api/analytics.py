from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User
from app.services.mock_cleanup import finalize_expired_mock_attempts
from app.schemas.analytics import (
    AttemptHistory,
    AttemptHistoryItem,
    OverviewStats,
    TopicPerformance,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewStats)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    finalize_expired_mock_attempts(db, current_user.id)
    attempts = db.query(Attempt).filter(Attempt.user_id == current_user.id)
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(Attempt.finished_at.isnot(None)).count()
    practice_attempts = attempts.filter(Attempt.mode == "practice").count()
    mock_attempts = attempts.filter(Attempt.mode == "mock").count()

    answer_stats = (
        db.query(
            func.count(AttemptAnswer.id).label("total"),
            func.sum(case((AttemptAnswer.is_correct.is_(True), 1), else_=0)).label("correct"),
        )
        .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
        .filter(Attempt.user_id == current_user.id)
        .first()
    )

    total_answered = answer_stats.total or 0
    total_correct = answer_stats.correct or 0
    overall_accuracy = round((total_correct / total_answered) * 100, 2) if total_answered else 0.0

    return OverviewStats(
        total_attempts=total_attempts,
        completed_attempts=completed_attempts,
        practice_attempts=practice_attempts,
        mock_attempts=mock_attempts,
        total_questions_answered=total_answered,
        total_correct=total_correct,
        overall_accuracy_percentage=overall_accuracy,
    )


def _topic_performance_query(db: Session, current_user: User):
    return (
        db.query(
            Topic.id.label("topic_id"),
            Topic.name.label("topic_name"),
            Subject.name.label("subject_name"),
            func.count(AttemptAnswer.id).label("total_answered"),
            func.sum(case((AttemptAnswer.is_correct.is_(True), 1), else_=0)).label("correct_answered"),
            func.max(Attempt.started_at).label("last_attempted_at"),
        )
        .join(Question, Question.id == AttemptAnswer.question_id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(Subject, Subject.id == Topic.subject_id)
        .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
        .filter(Attempt.user_id == current_user.id)
        .group_by(Topic.id, Topic.name, Subject.name)
    )


@router.get("/by-topic", response_model=List[TopicPerformance])
def get_performance_by_topic(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = _topic_performance_query(db, current_user).all()

    results = []
    for row in rows:
        accuracy = round((row.correct_answered / row.total_answered) * 100, 2) if row.total_answered else 0.0
        results.append(
            TopicPerformance(
                topic_id=row.topic_id,
                topic_name=row.topic_name,
                subject_name=row.subject_name,
                total_answered=row.total_answered,
                correct_answered=row.correct_answered,
                accuracy_percentage=accuracy,
                last_attempted_at=row.last_attempted_at,
            )
        )
    return sorted(results, key=lambda r: r.accuracy_percentage)


@router.get("/weak-topics", response_model=List[TopicPerformance])
def get_weak_topics(
    threshold_percentage: float = Query(default=60.0, ge=0, le=100),
    min_sample_size: int = Query(default=3, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A topic is flagged 'weak' only once there's enough data to trust the number —
    a single wrong answer on a brand-new topic isn't a meaningful signal yet."""
    rows = _topic_performance_query(db, current_user).all()

    weak = []
    for row in rows:
        if row.total_answered < min_sample_size:
            continue
        accuracy = round((row.correct_answered / row.total_answered) * 100, 2) if row.total_answered else 0.0
        if accuracy < threshold_percentage:
            weak.append(
                TopicPerformance(
                    topic_id=row.topic_id,
                    topic_name=row.topic_name,
                    subject_name=row.subject_name,
                    total_answered=row.total_answered,
                    correct_answered=row.correct_answered,
                    accuracy_percentage=accuracy,
                    last_attempted_at=row.last_attempted_at,
                )
            )

    return sorted(weak, key=lambda r: r.accuracy_percentage)


@router.get("/history", response_model=AttemptHistory)
def get_attempt_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    mode: Optional[str] = Query(default=None, pattern="^(practice|mock)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    finalize_expired_mock_attempts(db, current_user.id)
    query = (
        db.query(Attempt, Topic.name.label("topic_name"), Subject.name.label("subject_name"))
        .join(Topic, Topic.id == Attempt.topic_id)
        .join(Subject, Subject.id == Topic.subject_id)
        .filter(Attempt.user_id == current_user.id)
    )
    if mode:
        query = query.filter(Attempt.mode == mode)

    total = query.count()
    rows = query.order_by(Attempt.started_at.desc()).offset(offset).limit(limit).all()

    items = [
        AttemptHistoryItem(
            attempt_id=attempt.id,
            mode=attempt.mode,
            topic_name=topic_name,
            subject_name=subject_name,
            score_percentage=attempt.score_percentage,
            started_at=attempt.started_at,
            finished_at=attempt.finished_at,
        )
        for attempt, topic_name, subject_name in rows
    ]

    return AttemptHistory(total=total, items=items)
