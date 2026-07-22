import csv
import io
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin
from app.api.tutor import _call_gemini, _check_tutor_available
from app.core.time import utcnow
from app.db.session import get_db
from app.models.admin_document import AdminDocument
from app.models.option import Option
from app.models.pending_option import PendingOption
from app.models.pending_question import PendingQuestion
from app.models.question import Question
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User
from app.schemas.admin_content import (
    AdminDocumentOut,
    BulkImportResult,
    GeneratePendingRequest,
    PendingQuestionOut,
)
from app.services.note_extraction import MAX_UPLOAD_BYTES, extract_text_from_upload

router = APIRouter(prefix="/admin/content", tags=["admin-content"])


@router.post("/documents/upload", response_model=AdminDocumentOut)
async def upload_admin_document(
    file: UploadFile = File(...),
    document_type: str = Form(default="textbook"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large - please keep uploads under 5MB.")

    extracted_text = extract_text_from_upload(file.filename, content)

    document = AdminDocument(
        admin_user_id=admin.id,
        filename=file.filename,
        document_type=document_type,
        extracted_text=extracted_text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents", response_model=list[AdminDocumentOut])
def list_admin_documents(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(AdminDocument).order_by(AdminDocument.created_at.desc()).all()


@router.post("/generate", response_model=list[PendingQuestionOut])
def generate_pending_questions(
    payload: GeneratePendingRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _check_tutor_available(db, admin.id)

    document = db.query(AdminDocument).filter(AdminDocument.id == payload.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if document.document_type == "past_questions":
        instruction = (
            "The source material below contains PAST EXAM QUESTIONS. Do NOT copy any question "
            "verbatim. Instead, write NEW original questions that test the same underlying concepts "
            "and difficulty level, in your own wording, inspired by the patterns you see."
        )
    else:
        instruction = (
            "The source material below is textbook/study content. Write original exam-style "
            "questions covering the concepts it teaches."
        )

    system_prompt = (
        "You write NMCN (Nursing and Midwifery Council of Nigeria) exam-style practice questions "
        f"for the topic '{topic.name}'.\n\n{instruction}\n\n"
        "Respond with ONLY valid JSON, nothing else, using EXACTLY this structure "
        "(a single object with a questions key, not a bare array):\n"
        '{"questions": [{"stem": "...", "difficulty": "easy|medium|hard", "explanation": "...", '
        '"options": [{"text": "...", "is_correct": true|false}, ...]}]}\n\n'
        "Each question must have exactly 4 options with exactly ONE marked is_correct: true. "
        f"Generate up to {payload.count} questions."
    )

    reply_text = _call_gemini(
        system_prompt,
        f"Source material:\n\n{document.extracted_text}",
        response_mime_type="application/json",
        max_output_tokens=8000,
    )

    try:
        parsed = json.loads(reply_text or "{}")
        raw_questions = parsed if isinstance(parsed, list) else parsed["questions"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail=f"The AI didn't return usable questions - try again. ({exc})")

    created = []
    for raw_q in raw_questions:
        try:
            options = raw_q["options"]
            correct_count = sum(1 for o in options if o.get("is_correct"))
            if len(options) < 2 or correct_count != 1:
                continue
            pending = PendingQuestion(
                source_document_id=document.id,
                topic_id=topic.id,
                stem=raw_q["stem"],
                difficulty=raw_q.get("difficulty", "medium"),
                explanation=raw_q["explanation"],
            )
            pending.options = [
                PendingOption(text=o["text"], is_correct=bool(o.get("is_correct"))) for o in options
            ]
            db.add(pending)
            created.append(pending)
        except (KeyError, TypeError):
            continue

    if not created:
        raise HTTPException(status_code=502, detail="No well-formed questions were generated - try again.")

    db.commit()
    for q in created:
        db.refresh(q)
    return created


@router.get("/pending", response_model=list[PendingQuestionOut])
def list_pending_questions(
    topic_id: Optional[uuid.UUID] = None,
    status: str = "pending",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(PendingQuestion).options(joinedload(PendingQuestion.options)).filter(
        PendingQuestion.status == status
    )
    if topic_id:
        query = query.filter(PendingQuestion.topic_id == topic_id)
    return query.order_by(PendingQuestion.created_at.desc()).all()


def _get_pending_or_404(pending_id: uuid.UUID, db: Session) -> PendingQuestion:
    pending = (
        db.query(PendingQuestion)
        .options(joinedload(PendingQuestion.options))
        .filter(PendingQuestion.id == pending_id)
        .first()
    )
    if not pending:
        raise HTTPException(status_code=404, detail="Pending question not found")
    return pending


@router.post("/pending/{pending_id}/approve", response_model=PendingQuestionOut)
def approve_pending_question(
    pending_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    pending = _get_pending_or_404(pending_id, db)
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail=f"This question is already {pending.status}")

    question = Question(
        topic_id=pending.topic_id,
        stem=pending.stem,
        difficulty=pending.difficulty,
        explanation=pending.explanation,
    )
    question.options = [Option(text=o.text, is_correct=o.is_correct) for o in pending.options]
    db.add(question)

    pending.status = "approved"
    pending.reviewed_at = utcnow()
    db.commit()
    db.refresh(pending)
    return pending


@router.post("/pending/{pending_id}/reject", response_model=PendingQuestionOut)
def reject_pending_question(
    pending_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    pending = _get_pending_or_404(pending_id, db)
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail=f"This question is already {pending.status}")

    pending.status = "rejected"
    pending.reviewed_at = utcnow()
    db.commit()
    db.refresh(pending)
    return pending


@router.post("/bulk-import", response_model=BulkImportResult)
async def bulk_import_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = await file.read()
    text = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    created_count = 0
    skipped_rows = []

    for i, row in enumerate(reader, start=2):
        try:
            subject_name = row["subject"].strip()
            topic_name = row["topic"].strip()
            stem = row["stem"].strip()
            difficulty = (row.get("difficulty") or "medium").strip() or "medium"
            explanation = row["explanation"].strip()
            correct_letter = row["correct_answer"].strip().lower()

            option_texts = {}
            for letter in ("a", "b", "c", "d"):
                text_value = (row.get(f"option_{letter}") or "").strip()
                if text_value:
                    option_texts[letter] = text_value

            if len(option_texts) < 2 or correct_letter not in option_texts:
                skipped_rows.append(f"Row {i}: needs at least 2 options and a valid correct_answer")
                continue
            if difficulty not in ("easy", "medium", "hard"):
                difficulty = "medium"

            subject = db.query(Subject).filter(Subject.name == subject_name).first()
            if not subject:
                subject = Subject(name=subject_name)
                db.add(subject)
                db.flush()

            topic = (
                db.query(Topic)
                .filter(Topic.subject_id == subject.id, Topic.name == topic_name)
                .first()
            )
            if not topic:
                topic = Topic(subject_id=subject.id, name=topic_name)
                db.add(topic)
                db.flush()

            question = Question(
                topic_id=topic.id, stem=stem, difficulty=difficulty, explanation=explanation
            )
            question.options = [
                Option(text=text_value, is_correct=(letter == correct_letter))
                for letter, text_value in option_texts.items()
            ]
            db.add(question)
            created_count += 1
        except KeyError as exc:
            skipped_rows.append(f"Row {i}: missing required column {exc}")
        except Exception as exc:
            skipped_rows.append(f"Row {i}: {exc}")

    db.commit()
    return BulkImportResult(created_count=created_count, skipped_rows=skipped_rows)