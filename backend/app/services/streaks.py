from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.attempt import Attempt
from app.models.cbt_exam import CBTExamSession
from app.models.clinical_case_result import ClinicalCaseResult
from app.models.focus_session import FocusSession
from app.models.speed_round import SpeedRoundResult


def compute_streak(db: Session, user_id) -> tuple[int, bool]:
    """A day counts toward the streak if the student did ANY of: a practice
    attempt, a mock exam attempt, a speed round, a full CBT exam session, a
    clinical case simulation, or a completed focus session — not just one
    specific activity. Returns (current_streak_days, played_today)."""
    activity_dates = set()

    for (started_at,) in db.query(Attempt.started_at).filter(Attempt.user_id == user_id).all():
        if started_at:
            activity_dates.add(started_at.date())

    for (played_at,) in db.query(SpeedRoundResult.played_at).filter(SpeedRoundResult.user_id == user_id).all():
        if played_at:
            activity_dates.add(played_at.date())

    for (started_at,) in db.query(CBTExamSession.started_at).filter(CBTExamSession.user_id == user_id).all():
        if started_at:
            activity_dates.add(started_at.date())

    for (completed_at,) in (
        db.query(ClinicalCaseResult.completed_at).filter(ClinicalCaseResult.user_id == user_id).all()
    ):
        if completed_at:
            activity_dates.add(completed_at.date())

    for (completed_at,) in (
        db.query(FocusSession.completed_at).filter(FocusSession.user_id == user_id).all()
    ):
        if completed_at:
            activity_dates.add(completed_at.date())

    today = utcnow().date()
    played_today = today in activity_dates

    if not activity_dates:
        return 0, False

    cursor = today if played_today else today - timedelta(days=1)
    streak = 0
    while cursor in activity_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak, played_today
