import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.api.tutor import _check_tutor_available
from app.core.config import settings
from app.db.session import get_db
from app.models.clinical_case import ClinicalCase
from app.models.clinical_case_decision_point import ClinicalCaseDecisionPoint
from app.models.clinical_case_option import ClinicalCaseOption
from app.models.clinical_case_result import ClinicalCaseResult
from app.models.subject import Subject
from app.models.tutor_request import TutorRequest
from app.models.user import User
from app.schemas.clinical_case import (
    ClinicalCaseCompleteRequest,
    ClinicalCaseCompleteResponse,
    ClinicalCaseGenerateRequest,
    ClinicalCaseOut,
    ClinicalCaseSummary,
)
from app.services.streaks import compute_streak

router = APIRouter(prefix="/clinical-cases", tags=["clinical-cases"])


def _generate_case_json(subject_name: str | None) -> dict:
    context_line = (
        f"Focus the case on the subject area: {subject_name}.\n"
        if subject_name
        else "Choose any realistic general nursing subject area.\n"
    )
    system_prompt = (
        "You create realistic clinical case simulations for a Nigerian nursing student preparing "
        "for the NMCN Professional Qualifying Examination, to build clinical judgment rather than "
        "rote recall.\n\n"
        f"{context_line}"
        "Respond with ONLY valid JSON in this exact structure, nothing else:\n"
        '{"scenario": "...", "decision_points": [{"question": "...", "options": '
        '[{"text": "...", "is_correct": true|false, "rationale": "..."}]}]}\n\n'
        "The scenario should describe a patient presentation (age, chief complaint, relevant vitals "
        "and history) in 3-5 sentences. Include 4-5 decision_points representing the sequence of "
        "clinical decisions a nurse would make (initial assessment, prioritization, intervention, "
        "reassessment). Each decision point must have exactly 3 options with exactly ONE marked "
        "is_correct: true, and EVERY option (correct and incorrect) must have its own SHORT rationale "
        "(one sentence) explaining why it is or isn't the right clinical choice at that point in the "
        "case. Keep the whole response concise — short rationales, not paragraphs."
    )

    client = genai.Client(api_key=settings.google_api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents="Generate a clinical case simulation.",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=6000,
                thinking_config=types.ThinkingConfig(thinking_level=settings.gemini_thinking_level),
                response_mime_type="application/json",
            ),
        )
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Case generation failed: {exc}")

    try:
        parsed = json.loads(response.text or "{}")
        if not parsed.get("scenario") or not parsed.get("decision_points"):
            raise ValueError("missing scenario or decision_points")
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail=f"The AI didn't return a usable case — try again. ({exc})"
        )

    return parsed


@router.post("/generate", response_model=ClinicalCaseOut)
def generate_clinical_case(
    payload: ClinicalCaseGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_tutor_available(db, current_user.id)

    subject_name = None
    if payload.subject_id:
        subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_name = subject.name

    raw_case = _generate_case_json(subject_name)

    case = ClinicalCase(
        user_id=current_user.id,
        subject_context=subject_name,
        scenario=raw_case["scenario"],
    )
    db.add(case)
    db.flush()

    for i, dp in enumerate(raw_case["decision_points"]):
        options = dp.get("options", [])
        correct_count = sum(1 for o in options if o.get("is_correct"))
        if len(options) < 2 or correct_count != 1:
            continue  # skip malformed decision points rather than failing the whole case

        decision_point = ClinicalCaseDecisionPoint(case_id=case.id, order_index=i, question=dp["question"])
        decision_point.options = [
            ClinicalCaseOption(
                text=o["text"], is_correct=bool(o.get("is_correct")), rationale=o.get("rationale", "")
            )
            for o in options
        ]
        db.add(decision_point)

    db.add(TutorRequest(user_id=current_user.id))
    db.commit()
    db.refresh(case)

    if not case.decision_points:
        raise HTTPException(
            status_code=502, detail="The AI's response didn't contain any usable decision points — try again."
        )

    return case


@router.get("", response_model=list[ClinicalCaseSummary])
def list_clinical_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ClinicalCase)
        .filter(ClinicalCase.user_id == current_user.id)
        .order_by(ClinicalCase.created_at.desc())
        .all()
    )


@router.get("/{case_id}", response_model=ClinicalCaseOut)
def get_clinical_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = (
        db.query(ClinicalCase)
        .options(joinedload(ClinicalCase.decision_points).joinedload(ClinicalCaseDecisionPoint.options))
        .filter(ClinicalCase.id == case_id, ClinicalCase.user_id == current_user.id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Clinical case not found")
    return case


@router.post("/{case_id}/complete", response_model=ClinicalCaseCompleteResponse)
def complete_clinical_case(
    case_id: uuid.UUID,
    payload: ClinicalCaseCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = (
        db.query(ClinicalCase)
        .filter(ClinicalCase.id == case_id, ClinicalCase.user_id == current_user.id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Clinical case not found")
    if payload.correct_decisions > payload.total_decisions:
        raise HTTPException(status_code=400, detail="correct_decisions can't exceed total_decisions")

    score_percentage = round((payload.correct_decisions / payload.total_decisions) * 100, 2)
    db.add(
        ClinicalCaseResult(
            case_id=case_id,
            user_id=current_user.id,
            total_decisions=payload.total_decisions,
            correct_decisions=payload.correct_decisions,
            score_percentage=score_percentage,
        )
    )
    db.commit()

    streak, _ = compute_streak(db, current_user.id)
    return ClinicalCaseCompleteResponse(score_percentage=score_percentage, current_streak=streak)
