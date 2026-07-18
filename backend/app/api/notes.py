import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.api.tutor import _call_gemini, _check_tutor_available
from app.core.config import settings
from app.db.session import get_db
from app.models.generated_option import GeneratedOption
from app.models.generated_question import GeneratedQuestion
from app.models.note import UploadedNote
from app.models.tutor_request import TutorRequest
from app.models.user import User
from app.schemas.notes import (
    GenerateQuestionsRequest,
    GeneratedQuestionOut,
    NoteOut,
    NotesAskRequest,
)
from app.schemas.tutor import TutorAskResponse
from app.services.note_extraction import MAX_UPLOAD_BYTES, extract_text_from_upload

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/upload", response_model=NoteOut)
async def upload_note(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large — please keep uploads under 5MB.")

    extracted_text = extract_text_from_upload(file.filename, content)

    note = UploadedNote(
        user_id=current_user.id,
        filename=file.filename,
        extracted_text=extracted_text,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=List[NoteOut])
def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(UploadedNote)
        .filter(UploadedNote.user_id == current_user.id)
        .order_by(UploadedNote.created_at.desc())
        .all()
    )


def _generate_questions_json(note_text: str, count: int) -> list:
    system_prompt = (
        "You write NMCN (Nursing and Midwifery Council of Nigeria) exam-style practice questions "
        "based on a student's own study notes. Generate multiple-choice questions grounded ONLY in "
        "the material provided — do not introduce facts that aren't supported by the text. If the "
        "notes are too thin or unclear to generate a good question, generate fewer questions rather "
        "than inventing content.\n\n"
        "Respond with ONLY valid JSON in this exact structure, nothing else — no markdown, no "
        "commentary:\n"
        '{"questions": [{"stem": "...", "difficulty": "easy|medium|hard", "explanation": "...", '
        '"options": [{"text": "...", "is_correct": true|false}, ...]}]}\n\n'
        "Each question must have exactly 4 options with exactly ONE marked is_correct: true. "
        f"Generate up to {count} questions."
    )

    client = genai.Client(api_key=settings.google_api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"Student's notes:\n\n{note_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=3000,
                thinking_config=types.ThinkingConfig(thinking_level=settings.gemini_thinking_level),
                response_mime_type="application/json",
            ),
        )
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Question generation failed: {exc}")

    try:
        parsed = json.loads(response.text or "{}")
        questions = parsed["questions"]
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("empty questions list")
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"The AI didn't return usable questions from this text — try again. ({exc})",
        )

    return questions


@router.post("/{note_id}/generate-questions", response_model=List[GeneratedQuestionOut])
def generate_questions_from_note(
    note_id: uuid.UUID,
    payload: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_tutor_available(db, current_user.id)

    note = (
        db.query(UploadedNote)
        .filter(UploadedNote.id == note_id, UploadedNote.user_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    raw_questions = _generate_questions_json(note.extracted_text, payload.count)

    created = []
    for raw_q in raw_questions:
        try:
            stem = raw_q["stem"]
            explanation = raw_q["explanation"]
            difficulty = raw_q.get("difficulty", "medium")
            if difficulty not in ("easy", "medium", "hard"):
                difficulty = "medium"
            raw_options = raw_q["options"]
            correct_count = sum(1 for o in raw_options if o.get("is_correct"))
            if len(raw_options) < 2 or correct_count != 1:
                continue  # skip malformed questions rather than failing the whole batch
        except (KeyError, TypeError):
            continue

        question = GeneratedQuestion(
            note_id=note.id,
            user_id=current_user.id,
            stem=stem,
            difficulty=difficulty,
            explanation=explanation,
        )
        question.options = [
            GeneratedOption(text=o["text"], is_correct=bool(o.get("is_correct"))) for o in raw_options
        ]
        db.add(question)
        created.append(question)

    if not created:
        raise HTTPException(
            status_code=502,
            detail="The AI's response didn't contain any well-formed questions — try again.",
        )

    # Count this as one request against the shared daily Gemini budget, same
    # as /tutor/ask and /tutor/study-plan — one cost cap across every AI
    # feature, not a separate unprotected quota per feature.
    db.add(TutorRequest(user_id=current_user.id))
    db.commit()
    for q in created:
        db.refresh(q)

    return created


@router.get("/{note_id}/questions", response_model=List[GeneratedQuestionOut])
def get_generated_questions(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(UploadedNote)
        .filter(UploadedNote.id == note_id, UploadedNote.user_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return (
        db.query(GeneratedQuestion)
        .options(joinedload(GeneratedQuestion.options))
        .filter(GeneratedQuestion.note_id == note_id)
        .all()
    )


@router.post("/{note_id}/ask", response_model=TutorAskResponse)
def ask_about_note(
    note_id: uuid.UUID,
    payload: NotesAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Teaching mode grounded in a student's own uploaded notes — distinct
    from /tutor/ask (Module 14), which is grounded in the official question
    bank and requires having attempted a specific question first. This one
    is free-form, but strictly scoped to the content of one uploaded note."""
    _check_tutor_available(db, current_user.id)

    note = (
        db.query(UploadedNote)
        .filter(UploadedNote.id == note_id, UploadedNote.user_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    system_prompt = (
        "You are a patient, encouraging tutor helping a Nigerian nursing student prepare for the "
        "NMCN Professional Qualifying Examination. The student has uploaded their own study notes "
        "below, and is asking a question about them.\n\n"
        f"Student's notes:\n\n{note.extracted_text}\n\n"
        "Answer based on these notes wherever they cover the topic. If the student's question goes "
        "beyond what's in their notes, say so honestly rather than pretending the answer came from "
        "their material — you may still add general nursing knowledge to help, but clearly mark it "
        "as additional context beyond their notes, not something their notes already said. Keep your "
        "response under roughly 150 words unless the question genuinely needs more."
    )

    reply_text = _call_gemini(system_prompt, payload.message)

    db.add(TutorRequest(user_id=current_user.id))
    db.commit()

    return TutorAskResponse(reply=reply_text)
