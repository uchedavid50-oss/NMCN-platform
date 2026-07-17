from datetime import timedelta

from app.core.time import utcnow

from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.tutor_request import TutorRequest
from app.models.user import User
from app.schemas.tutor import TutorAskRequest, TutorAskResponse

router = APIRouter(prefix="/tutor", tags=["tutor"])

# Keeps a single free student well within Gemini's free-tier daily quota even
# on the stingiest model, while still allowing genuine back-and-forth study.
DAILY_TUTOR_LIMIT = 20


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


@router.post("/ask", response_model=TutorAskResponse)
def ask_tutor(
    payload: TutorAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.google_api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is not configured on the server. "
            "Set it in backend/.env before using the tutor.",
        )

    if _tutor_requests_today(db, current_user.id) >= DAILY_TUTOR_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"You've reached today's limit of {DAILY_TUTOR_LIMIT} tutor questions. "
                "This resets on a rolling 24-hour basis — try again a bit later."
            ),
        )

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

    client = genai.Client(api_key=settings.google_api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=payload.message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=settings.tutor_max_tokens,
            ),
        )
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Tutor request failed: {exc}")

    # Only log a "used request" once the call actually succeeded — a failed
    # Gemini call (e.g. transient 502) shouldn't count against the student's quota.
    db.add(TutorRequest(user_id=current_user.id))
    db.commit()

    reply_text = response.text or ""
    return TutorAskResponse(reply=reply_text)
