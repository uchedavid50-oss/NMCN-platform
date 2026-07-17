from datetime import timedelta

from app.core.time import utcnow

from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.analytics import _topic_performance_query
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.tutor_request import TutorRequest
from app.models.user import User
from app.schemas.tutor import StudyPlanResponse, TutorAskRequest, TutorAskResponse

router = APIRouter(prefix="/tutor", tags=["tutor"])

# Keeps a single free student well within Gemini's free-tier daily quota even
# on the stingiest model, while still allowing genuine back-and-forth study.
# Study plan requests count against this same limit as regular tutor questions
# — one shared budget for all Gemini usage per student, not separate quotas.
DAILY_TUTOR_LIMIT = 20

# Same thresholds as /analytics/weak-topics, so "what's weak" means the same
# thing whether a student is looking at their dashboard or asking the tutor.
WEAK_TOPIC_THRESHOLD_PERCENTAGE = 60.0
WEAK_TOPIC_MIN_SAMPLE_SIZE = 3


def _student_has_attempted(db: Session, user_id, question_id) -> bool:
    """Gate: the tutor only discusses a question with a student who has actually
    submitted an answer for it. Without this, /tutor/ask would be a backdoor to
    see the answer key without ever practicing — the exact class of leak we
    closed in Module 8, just via a different route."""
    return (
        db.query(AttemptAnswer)
        .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
        .filter(Attempt.user_id == user_id, AttemptAnswer.question_id == question_id)
        .first()
        is not None
    )


def _tutor_requests_today(db: Session, user_id) -> int:
    since = utcnow() - timedelta(hours=24)
    return (
        db.query(TutorRequest)
        .filter(TutorRequest.user_id == user_id, TutorRequest.created_at >= since)
        .count()
    )


def _check_tutor_available(db: Session, user_id) -> None:
    """Shared preflight check used by every endpoint that calls Gemini —
    keeps the "is this configured, has this student hit their limit" logic
    in one place instead of duplicated per endpoint."""
    if not settings.google_api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is not configured on the server. "
            "Set it in backend/.env before using the tutor.",
        )
    if _tutor_requests_today(db, user_id) >= DAILY_TUTOR_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"You've reached today's limit of {DAILY_TUTOR_LIMIT} tutor requests. "
                "This resets on a rolling 24-hour basis — try again a bit later."
            ),
        )


def _call_gemini(system_prompt: str, user_message: str) -> str:
    client = genai.Client(api_key=settings.google_api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=settings.tutor_max_tokens,
            ),
        )
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Tutor request failed: {exc}")
    return response.text or ""


@router.post("/ask", response_model=TutorAskResponse)
def ask_tutor(
    payload: TutorAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_tutor_available(db, current_user.id)

    question = (
        db.query(Question)
        .options(joinedload(Question.options), joinedload(Question.topic))
        .filter(Question.id == payload.question_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if not _student_has_attempted(db, current_user.id, payload.question_id):
        raise HTTPException(
            status_code=403,
            detail="Answer this question in practice or mock mode first, then ask the tutor about it.",
        )

    correct_option = next(o for o in question.options if o.is_correct)

    system_prompt = (
        "You are a patient, encouraging tutor helping a Nigerian nursing student prepare for the "
        "NMCN Professional Qualifying Examination. Stay strictly within nursing/NMCN exam content — "
        "if asked something unrelated, gently redirect back to exam prep.\n\n"
        f"Topic: {question.topic.name}\n"
        f"Question: {question.stem}\n"
        f"Correct answer: {correct_option.text}\n"
        f"Official explanation: {question.explanation}\n\n"
        "The student is asking a follow-up question about this. Don't just repeat the official "
        "explanation verbatim — elaborate, use a simple analogy or real clinical example where it "
        "helps, and check that everything you say is medically accurate. Keep your response under "
        "roughly 150 words unless the question genuinely needs more."
    )

    reply_text = _call_gemini(system_prompt, payload.message)

    # Only log a "used request" once the call actually succeeded — a failed
    # Gemini call (e.g. transient 502) shouldn't count against the student's quota.
    db.add(TutorRequest(user_id=current_user.id))
    db.commit()

    return TutorAskResponse(reply=reply_text)


@router.post("/study-plan", response_model=StudyPlanResponse)
def get_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fulfills the original charter's "recommend study plans" / "identify weak
    topics" goals for the AI Tutor, built directly on top of the same weak-topic
    logic from /analytics/weak-topics — "weak" means the same thing everywhere
    in this app, not a second definition invented just for this endpoint."""
    rows = _topic_performance_query(db, current_user).all()

    weak_rows = []
    for row in rows:
        if row.total_answered < WEAK_TOPIC_MIN_SAMPLE_SIZE:
            continue
        accuracy = round((row.correct_answered / row.total_answered) * 100, 2) if row.total_answered else 0.0
        if accuracy < WEAK_TOPIC_THRESHOLD_PERCENTAGE:
            weak_rows.append((row.topic_name, row.subject_name, accuracy))

    if not weak_rows:
        # No Gemini call needed (and no cost) for the "nothing weak yet" case —
        # either the student hasn't practiced enough yet, or is doing fine.
        return StudyPlanResponse(
            has_weak_topics=False,
            weak_topic_names=[],
            plan=(
                "You don't have any topics flagged as weak yet — either you haven't practiced "
                "enough questions in a topic to tell (answer at least 3 in one topic), or you're "
                "doing well across the board. Keep practicing across different topics and check "
                "back here once you've built up more attempts."
            ),
        )

    _check_tutor_available(db, current_user.id)

    weak_rows.sort(key=lambda r: r[2])  # weakest first
    topic_summary = "\n".join(f"- {name} ({subject}): {acc}% accuracy" for name, subject, acc in weak_rows)

    system_prompt = (
        "You are a patient, encouraging tutor helping a Nigerian nursing student prepare for the "
        "NMCN Professional Qualifying Examination. Stay strictly within nursing/NMCN exam content.\n\n"
        f"Here are the student's weakest topics based on real practice data:\n{topic_summary}\n\n"
        "Write a short, encouraging, practical study plan (under 200 words) that: names their weakest "
        "topic first and suggests a concrete next study action for it, briefly covers the other weak "
        "topics too, and ends with one encouraging sentence. Don't be generic — reference the actual "
        "topic names given above."
    )

    reply_text = _call_gemini(system_prompt, "Please generate my study plan.")

    db.add(TutorRequest(user_id=current_user.id))
    db.commit()

    return StudyPlanResponse(
        has_weak_topics=True,
        weak_topic_names=[name for name, _, _ in weak_rows],
        plan=reply_text,
    )
