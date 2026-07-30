import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin, get_current_user
from app.db.session import get_db
from app.models.ai_provider_attempt import AIProviderAttempt
from app.models.entrance_exam_generation_request import EntranceExamGenerationRequest
from app.models.entrance_exam_question import EntranceExamQuestion
from app.models.user import User
from app.schemas.entrance_exam import (
    ENTRANCE_EXAM_SUBJECTS,
    EntranceExamQuestionOut,
    GenerateBatchResult,
    GenerateEntranceExamRequest,
    ProviderStatusOut,
)
from app.services.ai_router import PROVIDERS, FALLBACK_MESSAGE, call_ai_router_parallel


def _normalize_question_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".!?")


def _extract_json_object(text: str) -> str:
    """Gemini's response_mime_type="application/json" enforces clean output,
    but not every provider has an equivalent structured-output mode -- some
    wrap the JSON in markdown code fences or a leading sentence. Strip those
    so json.JSONDecoder().raw_decode (which requires valid JSON starting at
    position 0) has a clean string to work with."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    brace_index = text.find("{")
    if brace_index > 0:
        text = text[brace_index:]
    return text

router = APIRouter(prefix="/entrance-exam", tags=["entrance-exam"])


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


@router.post("/generate", response_model=GenerateBatchResult)
def generate_entrance_exam_questions(
    payload: GenerateEntranceExamRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-only -- students only ever see questions already stored in
    the database (see /entrance-exam/questions), never trigger an AI call
    themselves. No per-admin rate limit here (trusted actor, not a student
    who could otherwise spam this) -- cost protection is the per-provider
    daily cap in ai_router.py instead. Fans out to every eligible provider
    in parallel (see call_ai_router_parallel) instead of trying one at a
    time; each provider that succeeds contributes up to 20 questions,
    deduped by normalized text across all providers before saving."""
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
        "sentence or two. Generate 20 questions."
    )

    provider_results = call_ai_router_parallel(
        db, system_prompt, f"Subject: {payload.subject}", response_mime_type="application/json"
    )

    results_out = []
    all_valid_questions = []  # list of (provider_name, raw_question_dict), pre-dedup
    any_provider_returned_text = False

    for result in provider_results:
        raw_count = 0
        if result.status == "success":
            any_provider_returned_text = True
            try:
                cleaned = _extract_json_object(result.raw_text or "{}")
                parsed, _ = json.JSONDecoder().raw_decode(cleaned)
                raw_questions = parsed if isinstance(parsed, list) else parsed["questions"]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                raw_questions = []

            for raw_q in raw_questions:
                if (
                    isinstance(raw_q, dict)
                    and raw_q.get("question_text")
                    and raw_q.get("model_answer")
                    and raw_q.get("explanation")
                ):
                    all_valid_questions.append((result.provider, raw_q))
                    raw_count += 1

        results_out.append(
            {
                "provider": result.provider,
                "status": result.status,
                "questions_generated": raw_count,
                "elapsed_seconds": round(result.elapsed_seconds, 2),
                "error": result.error,
            }
        )

    seen_normalized: set[str] = set()
    to_save = []
    for provider_name, raw_q in all_valid_questions:
        normalized = _normalize_question_text(raw_q["question_text"])
        if normalized in seen_normalized:
            continue
        seen_normalized.add(normalized)
        to_save.append(
            EntranceExamQuestion(
                subject=payload.subject,
                question_type=raw_q.get("question_type", "short_answer"),
                question_text=raw_q["question_text"],
                model_answer=raw_q["model_answer"],
                explanation=raw_q["explanation"],
                provider=provider_name,
            )
        )

    if not to_save:
        if any_provider_returned_text:
            raise HTTPException(status_code=502, detail="No well-formed questions were generated - try again.")
        raise HTTPException(status_code=502, detail=FALLBACK_MESSAGE)

    for question in to_save:
        db.add(question)
    db.add(EntranceExamGenerationRequest(user_id=admin.id))
    db.commit()
    for q in to_save:
        db.refresh(q)

    return {
        "results": results_out,
        "saved_questions": to_save,
        "total_saved": len(to_save),
        "total_generated_before_dedup": len(all_valid_questions),
    }


@router.get("/admin/provider-status", response_model=ProviderStatusOut)
def get_provider_status(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    providers = []
    for provider in PROVIDERS:
        last_attempt = (
            db.query(AIProviderAttempt)
            .filter(AIProviderAttempt.provider == provider.name)
            .order_by(AIProviderAttempt.created_at.desc())
            .first()
        )
        if last_attempt is None:
            status = "unknown"
        else:
            status = "healthy" if last_attempt.success else "failing"
        providers.append(
            {
                "name": provider.name,
                "configured": provider.is_configured(),
                "status": status,
                "last_attempt_at": last_attempt.created_at if last_attempt else None,
                "last_error": last_attempt.error if last_attempt and not last_attempt.success else None,
            }
        )

    last_success = (
        db.query(AIProviderAttempt)
        .filter(AIProviderAttempt.success.is_(True))
        .order_by(AIProviderAttempt.created_at.desc())
        .first()
    )
    last_used = {"provider": last_success.provider, "at": last_success.created_at} if last_success else None

    question_counts = [
        {
            "subject": subject,
            "count": db.query(EntranceExamQuestion).filter(EntranceExamQuestion.subject == subject).count(),
        }
        for subject in ENTRANCE_EXAM_SUBJECTS
    ]

    return {"providers": providers, "last_used": last_used, "question_counts": question_counts}


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
