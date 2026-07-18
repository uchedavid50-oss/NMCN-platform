from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.cbt_exam import CBTExamSession
from app.models.cbt_exam_answer import CBTExamAnswer


def finalize_expired_cbt_sessions(db: Session, user_id) -> int:
    """Same idea as finalize_expired_mock_attempts (Module 17), but scored
    against the session's own stored question_ids count, not however many
    questions exist for a topic — a full CBT session's "total_questions" is
    whatever was actually sampled at start time."""
    expired = (
        db.query(CBTExamSession)
        .filter(
            CBTExamSession.user_id == user_id,
            CBTExamSession.finished_at.is_(None),
            CBTExamSession.expires_at < utcnow(),
        )
        .all()
    )

    for session in expired:
        total_questions = len(session.question_ids)
        correct_count = (
            db.query(CBTExamAnswer)
            .filter(CBTExamAnswer.session_id == session.id, CBTExamAnswer.is_correct.is_(True))
            .count()
        )
        score = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0

        session.finished_at = session.expires_at
        session.score_percentage = score

    if expired:
        db.commit()

    return len(expired)
