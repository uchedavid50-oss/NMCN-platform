import json
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin, get_current_user
from app.api.tutor import _call_gemini
from app.core.config import settings
from app.core.time import utcnow
from app.db.session import get_db
from app.models.entrance_exam_generation_request import EntranceExamGenerationRequest
from app.models.entrance_exam_question import EntranceExamQuestion
from app.models.user import User
from app.schemas.entrance_exam import EntranceExamQuestionOut, GenerateEntranceExamRequest

router = APIRouter(prefix="/entrance-exam", tags=["entrance-exam"])

# Separate budget from the tutor's DAILY_TUTOR_LIMIT (see tutor.py) so
# generating entrance-exam questions doesn't compete with a student's
# tutor-chat quota. Each generation call produces ~8-10 questions, so 5
# calls/day is a generous ceiling for one student.
DAILY_ENTRANCE_GEN_LIMIT = 5


def _entrance_gen_requests_today(db: Session, user_id) -> int:
    since = utcnow() - timedelta(hours=24)
    return (
        db.query(EntranceExamGenerationRequest)
        .filter(
            EntranceExamGenerationRequest.user_id == user_id,
            EntranceExamGenerationRequest.created_at >= since,
        )
        .count()
    )


def _check_entrance_exam_available(db: Session, user_id) -> None:
    if not settings.google_api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is not configured on the server.",
        )
    if _entrance_gen_requests_today(db, user_id) >= DAILY_ENTRANCE_GEN_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"You've reached today's limit of {DAILY_ENTRANCE_GEN_LIMIT} "
                "question-generation requests. This resets on a rolling "
                "24-hour basis — try again a bit later."
            ),
        )


@router.get("/questions", response_model=list[EntranceExamQuestionOut])
def list_entrance_exam_questions(
    subject: str,
    count: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    questions = (
        db.query(EntranceExamQuestion)
        .filter(EntranceExamQuestion.subject == subject)
        .order_by(func.random())
        .limit(count)
        .all()
    )
    if not questions:
        raise HTTPException(
            status_code=400,
            detail=f"No {subject} questions yet — generate some first.",
        )
    return questions


@router.post("/generate", response_model=list[EntranceExamQuestionOut])
def generate_entrance_exam_questions(
    payload: GenerateEntranceExamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Both students (via the "Generate More Questions" button) and admins
    can call this -- gated by the same per-user rolling-24h limit either
    way, consistent with how admin content generation elsewhere in the app
    also goes through its own usage gate rather than being exempt."""
    _check_entrance_exam_available(db, current_user.id)

    system_prompt = (
        f"You write past-question-bank style practice questions for the {payload.subject} "
        "section of a Nigerian nursing school entrance examination (pre-nursing / "
        "secondary-school leaving level, similar in spirit to JAMB-style entrance exams). "
        "Do NOT write multiple-choice questions. Every question must be one of: a short-answer "
        "question, a fill-in-the-blank question (use a blank like ______ in the question text), "
        "or a short theory/essay-style question. Cover a range of core topics a candidate would "
        "be expected to know for this subject at that level.\n\n"
        "Respond with ONLY valid JSON, nothing else, using EXACTLY this structure "
        "(a single object with a questions key, not a bare array):\n"
        '{"questions": [{"question_type": "short_answer|fill_blank|theory", '
        '"question_text": "...", "model_answer": "...", "explanation": "..."}]}\n\n'
        "model_answer should be the concise correct answer (or, for theory questions, a model "
        "answer covering the key points expected). explanation should briefly explain why, in a "
        "sentence or two. Generate 8 to 10 questions."
    )

    reply_text = _call_gemini(
        system_prompt,
        f"Subject: {payload.subject}",
        response_mime_type="application/json",
        max_output_tokens=4000,
    )

    try:
        parsed, _ = json.JSONDecoder().raw_decode((reply_text or "{}").strip())
        raw_questions = parsed if isinstance(parsed, list) else parsed["questions"]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"The AI didn't return usable questions - try again. ({exc})")

    created = []
    for raw_q in raw_questions:
        try:
            question = EntranceExamQuestion(
                subject=payload.subject,
                question_type=raw_q.get("question_type", "short_answer"),
                question_text=raw_q["question_text"],
                model_answer=raw_q["model_answer"],
                explanation=raw_q["explanation"],
            )
            db.add(question)
            created.append(question)
        except (KeyError, TypeError):
            continue

    if not created:
        raise HTTPException(status_code=502, detail="No well-formed questions were generated - try again.")

    db.add(EntranceExamGenerationRequest(user_id=current_user.id))
    db.commit()
    for q in created:
        db.refresh(q)
    return created


@router.delete("/questions/{question_id}", status_code=204)
def delete_entrance_exam_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = db.query(EntranceExamQuestion).filter(EntranceExamQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)
    db.commit()
