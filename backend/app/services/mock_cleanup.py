from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question


def finalize_expired_mock_attempts(db: Session, user_id) -> int:
    """Closes the "stale mock attempt" gap flagged since Module 5: there's no
    background job to auto-submit a mock exam the moment its timer runs out,
    so an abandoned attempt would otherwise sit forever with finished_at=None,
    showing as "incomplete" in history/analytics even though its time is long
    gone (this is exactly what the analytics dashboard testing in Module 13
    surfaced — 13 mock attempts, 1 finished).

    Rather than adding a scheduler, this runs lazily: any time a user's mock
    attempts get touched (status check, or their own analytics), we first
    finalize anything that's expired but was never submitted, scoring it
    based on whatever answers exist. Returns how many were finalized.
    """
    expired = (
        db.query(Attempt)
        .filter(
            Attempt.user_id == user_id,
            Attempt.mode == "mock",
            Attempt.finished_at.is_(None),
            Attempt.expires_at < utcnow(),
        )
        .all()
    )

    for attempt in expired:
        total_questions = db.query(Question).filter(Question.topic_id == attempt.topic_id).count()
        correct_count = (
            db.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_id == attempt.id, AttemptAnswer.is_correct.is_(True))
            .count()
        )
        score = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0

        # Mark it finished at the moment it actually expired, not "now" — this
        # keeps history timestamps honest rather than showing a finish time
        # that's however long after the student actually walked away.
        attempt.finished_at = attempt.expires_at
        attempt.score_percentage = score

    if expired:
        db.commit()

    return len(expired)
