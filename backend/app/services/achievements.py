from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.subject import Subject
from app.models.topic import Topic
from app.services.streaks import compute_streak

SUBJECT_MASTERY_THRESHOLD = 80.0
SUBJECT_MASTERY_MIN_SAMPLE = 10


def _subject_mastery(db: Session, user_id) -> list[str]:
    rows = (
        db.query(
            Subject.name.label("subject_name"),
            func.count(AttemptAnswer.id).label("total_answered"),
            func.sum(case((AttemptAnswer.is_correct.is_(True), 1), else_=0)).label("correct_answered"),
        )
        .join(Question, Question.id == AttemptAnswer.question_id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(Subject, Subject.id == Topic.subject_id)
        .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
        .filter(Attempt.user_id == user_id)
        .group_by(Subject.name)
        .all()
    )

    mastered = []
    for row in rows:
        if row.total_answered < SUBJECT_MASTERY_MIN_SAMPLE:
            continue
        accuracy = (row.correct_answered / row.total_answered) * 100
        if accuracy >= SUBJECT_MASTERY_THRESHOLD:
            mastered.append(row.subject_name)
    return mastered


def compute_badges(db: Session, user_id) -> list[dict]:
    practice_count = db.query(Attempt).filter(Attempt.user_id == user_id, Attempt.mode == "practice").count()
    finished_mock_count = (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id, Attempt.mode == "mock", Attempt.finished_at.isnot(None))
        .count()
    )
    perfect_mock = (
        db.query(Attempt)
        .filter(
            Attempt.user_id == user_id,
            Attempt.mode == "mock",
            Attempt.score_percentage == 100.0,
        )
        .first()
        is not None
    )

    answer_stats = (
        db.query(func.count(AttemptAnswer.id))
        .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
        .filter(Attempt.user_id == user_id)
        .scalar()
    )
    total_answered = answer_stats or 0

    streak, _ = compute_streak(db, user_id)
    mastered_subjects = _subject_mastery(db, user_id)

    badges = [
        {
            "id": "first_steps",
            "name": "First Steps",
            "description": "Complete your first practice question",
            "earned": total_answered > 0,
        },
        {
            "id": "mock_ready",
            "name": "Mock Ready",
            "description": "Finish your first mock exam",
            "earned": finished_mock_count > 0,
        },
        {
            "id": "century_club",
            "name": "Century Club",
            "description": "Answer 100 questions total",
            "earned": total_answered >= 100,
        },
        {
            "id": "perfectionist",
            "name": "Perfectionist",
            "description": "Score 100% on a mock exam",
            "earned": perfect_mock,
        },
        {
            "id": "week_streak",
            "name": "7-Day Warrior",
            "description": "Keep a 7-day practice streak",
            "earned": streak >= 7,
        },
        {
            "id": "month_streak",
            "name": "30-Day Legend",
            "description": "Keep a 30-day practice streak",
            "earned": streak >= 30,
        },
    ]

    for subject_name in mastered_subjects:
        badges.append(
            {
                "id": f"mastery_{subject_name.lower().replace(' ', '_')}",
                "name": f"{subject_name} Mastery",
                "description": f"80%+ accuracy across {subject_name}, with enough questions answered to trust it",
                "earned": True,
            }
        )

    return badges


def is_eligible_for_certificate(db: Session, user_id) -> tuple[bool, str]:
    """Deliberately conservative criteria — this certificate represents genuine,
    sustained engagement with the platform, not a rubber stamp. It is NOT an
    official NMCN credential and must never be presented as one."""
    finished_mocks = (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id, Attempt.mode == "mock", Attempt.finished_at.isnot(None))
        .all()
    )
    if len(finished_mocks) < 3:
        return False, f"Complete at least 3 mock exams (you've finished {len(finished_mocks)})."

    avg_score = sum(a.score_percentage or 0 for a in finished_mocks) / len(finished_mocks)
    if avg_score < 70.0:
        return False, f"Average mock exam score must be at least 70% (currently {avg_score:.1f}%)."

    return True, "Eligible."
