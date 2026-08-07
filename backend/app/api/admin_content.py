import csv
import io
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin
from app.api.tutor import _check_tutor_available
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
from app.services.ai_router import FALLBACK_MESSAGE, call_ai_router_parallel, extract_json_object
from app.services.note_extraction import MAX_UPLOAD_BYTES, extract_text_from_upload

router = APIRouter(prefix="/admin/content", tags=["admin-content"])

EXAM_FRAMING = {
    "NMCN": {
        "context": "the NMCN (Nursing and Midwifery Council of Nigeria) Professional Qualifying Examination",
        "tip_label": "NMCN Tip",
        "tip_instruction": (
            "Write exam_specific_tip for the Nigerian PQE specifically: reference NMCN's scope of "
            "practice, Nigerian healthcare protocols and facility conventions, and local drug naming "
            "as used in Nigerian clinical practice where relevant."
        ),
    },
    "NCLEX": {
        "context": "the NCLEX (National Council Licensure Examination) for nursing licensure",
        "tip_label": "NCLEX Tip",
        "tip_instruction": (
            "Write exam_specific_tip for the US NCLEX specifically: reference US scope of practice, "
            "US-standard drug names, and NCLEX question-style conventions (e.g. Select All That Apply, "
            "prioritization/delegation framing) where relevant."
        ),
    },
}


@router.patch("/subjects/{subject_id}/exam-type")
def set_subject_exam_type(
    subject_id: uuid.UUID,
    exam_type: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if exam_type not in EXAM_FRAMING:
        raise HTTPException(status_code=400, detail=f"exam_type must be one of {list(EXAM_FRAMING)}")
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject.exam_type = exam_type
    db.commit()
    return {"id": str(subject.id), "name": subject.name, "exam_type": subject.exam_type}


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


def _generate_questions_for_topic(
    db: Session,
    topic: Topic,
    count: int,
    document: Optional[AdminDocument] = None,
    extraction_mode: str = "ai_generate",
    exam_type_override: Optional[str] = None,
) -> tuple[list[PendingQuestion], str]:
    """Core question-generation logic shared by the /generate endpoint and the
    bulk generate_all_questions.py script. Adds PendingQuestion rows to `db`
    (not committed -- caller decides commit granularity) and returns them
    along with the exam_type actually used for framing.

    exam_type_override forces NMCN/NCLEX framing regardless of the topic's
    subject.exam_type -- used by the bulk script to generate NCLEX-style
    content across topics that are tagged NMCN by default."""
    exam_type = exam_type_override or (topic.subject.exam_type if topic.subject else "NMCN")
    exam_config = EXAM_FRAMING.get(exam_type, EXAM_FRAMING["NMCN"])

    if document is None:
        instruction = (
            "No source document was provided. Use your own nursing knowledge to write "
            "original, accurate exam-style questions on this topic."
        )
        source_material = f"Topic: {topic.name} (Subject: {topic.subject.name if topic.subject else 'General'})"
    elif extraction_mode == "verbatim" and document.document_type == "past_questions":
        instruction = (
            "The source material below contains PAST EXAM QUESTIONS. Extract each question "
            "EXACTLY as written — same wording, same options, same order. Do NOT paraphrase, "
            "reword, or invent new questions. If the source includes a rationale/explanation "
            "for the correct answer, copy that rationale verbatim too. If a question has no "
            "explanation in the source, write a brief factual explanation of why the correct "
            "answer is correct, based only on the source content."
        )
        source_material = f"Source material:\n\n{document.extracted_text}"
    elif document.document_type == "past_questions":
        instruction = (
            "The source material below contains PAST EXAM QUESTIONS. Do NOT copy any question "
            "verbatim. Instead, write NEW original questions that test the same underlying concepts "
            "and difficulty level, in your own wording, inspired by the patterns you see."
        )
        source_material = f"Source material:\n\n{document.extracted_text}"
    else:
        instruction = (
            "The source material below is textbook/study content. Write original exam-style "
            "questions covering the concepts it teaches."
        )
        source_material = f"Source material:\n\n{document.extracted_text}"

    system_prompt = (
        f"You write rich, exam-style practice questions for a nursing student preparing for "
        f"{exam_config['context']}, on the topic '{topic.name}'.\n\n{instruction}\n\n"
        "For EACH question, provide:\n"
        "- stem, difficulty (easy|medium|hard), and exactly 4 options with exactly ONE marked "
        "is_correct: true.\n"
        "- explanation: a detailed rationale for the correct answer that explains the underlying "
        "clinical reasoning, not just a restatement of the stem.\n"
        "- why_others_wrong: a JSON object with one entry per INCORRECT option, keyed by that "
        "option's letter position among the 4 options listed (A = 1st option, B = 2nd, C = 3rd, "
        "D = 4th) -- omit the key for the correct option. Each value explains specifically why "
        "that option is wrong.\n"
        "- clinical_tip: a short, memorable, exam-focused tip tied to the underlying concept "
        "(not specific to either exam body).\n"
        f"- exam_specific_tip: {exam_config['tip_instruction']}\n"
        "- cognitive_level: one of Knowledge, Application, Analysis.\n\n"
        "Respond with ONLY valid JSON, nothing else, using EXACTLY this structure "
        "(a single object with a questions key, not a bare array):\n"
        '{"questions": [{"stem": "...", "difficulty": "easy|medium|hard", '
        '"options": [{"text": "...", "is_correct": true|false}, ...], "explanation": "...", '
        '"why_others_wrong": {"A": "...", "B": "...", "C": "..."}, "clinical_tip": "...", '
        '"exam_specific_tip": "...", "cognitive_level": "Knowledge|Application|Analysis"}]}\n\n'
        f"Generate up to {count} questions."
    )

    # Fans out to every configured, under-quota provider (see ai_router.py) instead
    # of calling Gemini alone -- takes the first provider whose response parses into
    # at least one well-formed question, rather than merging multiple providers'
    # output (unlike entrance-exam generation), since a mismatched/lower-quality
    # provider producing malformed rationale/tip fields is worse here than just
    # falling through to the next provider.
    provider_results = call_ai_router_parallel(
        db, system_prompt, source_material, response_mime_type="application/json"
    )

    raw_questions = None
    any_success = False
    last_error: Exception | None = None
    for result in provider_results:
        if result.status != "success":
            continue
        any_success = True
        try:
            cleaned = extract_json_object(result.raw_text or "{}")
            parsed, _ = json.JSONDecoder().raw_decode(cleaned)
            candidate = parsed if isinstance(parsed, list) else parsed["questions"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            last_error = exc
            continue
        if candidate:
            raw_questions = candidate
            break

    if raw_questions is None:
        if any_success:
            raise HTTPException(
                status_code=502, detail=f"No provider returned usable questions - try again. ({last_error})"
            )
        raise HTTPException(status_code=502, detail=FALLBACK_MESSAGE)

    created = []
    for raw_q in raw_questions:
        try:
            options = raw_q["options"]
            correct_count = sum(1 for o in options if o.get("is_correct"))
            if len(options) < 2 or correct_count != 1:
                continue
            why_others_wrong = raw_q.get("why_others_wrong")
            pending = PendingQuestion(
                source_document_id=document.id if document else None,
                topic_id=topic.id,
                stem=raw_q["stem"],
                difficulty=raw_q.get("difficulty", "medium"),
                explanation=raw_q["explanation"],
                why_others_wrong=json.dumps(why_others_wrong) if isinstance(why_others_wrong, dict) else None,
                clinical_tip=raw_q.get("clinical_tip"),
                exam_specific_tip=raw_q.get("exam_specific_tip"),
                cognitive_level=raw_q.get("cognitive_level"),
                source="past_questions" if document and document.document_type == "past_questions" else None,
            )
            pending.options = [
                PendingOption(text=o["text"], is_correct=bool(o.get("is_correct"))) for o in options
            ]
            db.add(pending)
            created.append(pending)
        except (KeyError, TypeError):
            continue

    return created, exam_type


@router.post("/generate", response_model=list[PendingQuestionOut])
def generate_pending_questions(
    payload: GeneratePendingRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _check_tutor_available(db, admin.id)

    document = None
    if payload.document_id:
        document = db.query(AdminDocument).filter(AdminDocument.id == payload.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

    topic = (
        db.query(Topic)
        .options(joinedload(Topic.subject))
        .filter(Topic.id == payload.topic_id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    created, exam_type = _generate_questions_for_topic(
        db, topic, payload.count, document=document, extraction_mode=payload.extraction_mode
    )

    if not created:
        raise HTTPException(status_code=502, detail="No well-formed questions were generated - try again.")

    db.commit()
    for q in created:
        db.refresh(q)
        q.exam_type = exam_type
    return created


def _attach_exam_type(pending_list: list[PendingQuestion]) -> list[PendingQuestion]:
    for p in pending_list:
        p.exam_type = p.topic.subject.exam_type if p.topic and p.topic.subject else "NMCN"
    return pending_list


@router.get("/pending", response_model=list[PendingQuestionOut])
def list_pending_questions(
    topic_id: Optional[uuid.UUID] = None,
    status: str = "pending",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = (
        db.query(PendingQuestion)
        .options(
            joinedload(PendingQuestion.options),
            joinedload(PendingQuestion.topic).joinedload(Topic.subject),
        )
        .filter(PendingQuestion.status == status)
    )
    if topic_id:
        query = query.filter(PendingQuestion.topic_id == topic_id)
    results = query.order_by(PendingQuestion.created_at.desc()).all()
    return _attach_exam_type(results)


def _get_pending_or_404(pending_id: uuid.UUID, db: Session) -> PendingQuestion:
    pending = (
        db.query(PendingQuestion)
        .options(
            joinedload(PendingQuestion.options),
            joinedload(PendingQuestion.topic).joinedload(Topic.subject),
        )
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
        why_others_wrong=pending.why_others_wrong,
        clinical_tip=pending.clinical_tip,
        exam_specific_tip=pending.exam_specific_tip,
        cognitive_level=pending.cognitive_level,
        source=pending.source,
    )
    question.options = [Option(text=o.text, is_correct=o.is_correct) for o in pending.options]
    db.add(question)

    pending.status = "approved"
    pending.reviewed_at = utcnow()
    db.commit()
    db.refresh(pending)
    _attach_exam_type([pending])
    return pending


@router.post("/pending/approve-all")
def approve_all_pending_questions(
    topic_id: uuid.UUID | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Bulk-publishes pending questions (optionally scoped to one topic)
    straight into the official bank, skipping individual review. A
    deliberate trade-off: faster at volume, but gives up the per-question
    quality check the review queue exists for. Use when you've already
    spot-checked enough batches to trust the pattern, not as a default.

    Processes at most `limit` per call -- at 1000+ pending questions, doing
    them all in one request/transaction was slow enough to look hung to the
    caller. The frontend calls this repeatedly (like bulk-generate) until
    remaining_count hits 0."""
    base_query = db.query(PendingQuestion).filter(PendingQuestion.status == "pending")
    if topic_id:
        base_query = base_query.filter(PendingQuestion.topic_id == topic_id)

    pending_list = (
        base_query.options(joinedload(PendingQuestion.options))
        .order_by(PendingQuestion.created_at)
        .limit(limit)
        .all()
    )
    approved_count = 0

    for pending in pending_list:
        question = Question(
            topic_id=pending.topic_id,
            stem=pending.stem,
            difficulty=pending.difficulty,
            explanation=pending.explanation,
            why_others_wrong=pending.why_others_wrong,
            clinical_tip=pending.clinical_tip,
            exam_specific_tip=pending.exam_specific_tip,
            cognitive_level=pending.cognitive_level,
            source=pending.source,
        )
        question.options = [Option(text=o.text, is_correct=o.is_correct) for o in pending.options]
        db.add(question)
        pending.status = "approved"
        pending.reviewed_at = utcnow()
        approved_count += 1

    db.commit()
    remaining_count = base_query.count()
    return {"approved_count": approved_count, "remaining_count": remaining_count}


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
