import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.api.tutor import _call_gemini, _check_tutor_available
from app.db.session import get_db
from app.models.pending_option import PendingOption
from app.models.pending_question import PendingQuestion
from app.models.textbook import Textbook
from app.models.textbook_folder import TextbookFolder
from app.models.topic import Topic
from app.models.user import User
from app.schemas.textbook import TextbookFolderCreate, TextbookFolderOut, TextbookOut
from app.schemas.admin_content import PendingQuestionOut
from app.services.note_extraction import extract_text_from_upload

router = APIRouter(prefix="/textbooks", tags=["textbooks"])

MAX_TEXTBOOK_BYTES = 20 * 1024 * 1024  # 20MB - textbooks are naturally larger than study notes


class GenerateFromTextbookRequest(BaseModel):
    topic_id: uuid.UUID
    count: int = Field(default=20, ge=1, le=30)


@router.post("/folders", response_model=TextbookFolderOut, status_code=201)
def create_folder(
    payload: TextbookFolderCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = db.query(TextbookFolder).filter(TextbookFolder.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="A folder with this name already exists")
    folder = TextbookFolder(name=payload.name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("/folders", response_model=list[TextbookFolderOut])
def list_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(TextbookFolder).order_by(TextbookFolder.name.asc()).all()


@router.post("/folders/{folder_id}/upload", response_model=TextbookOut, status_code=201)
async def upload_textbook(
    folder_id: uuid.UUID,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    folder = db.query(TextbookFolder).filter(TextbookFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    content = await file.read()
    if len(content) > MAX_TEXTBOOK_BYTES:
        raise HTTPException(status_code=400, detail="File too large - please keep uploads under 20MB.")
    textbook = Textbook(
        folder_id=folder.id,
        title=title,
        filename=file.filename,
        content_type=file.content_type or "application/pdf",
        file_size=len(content),
        file_data=content,
        uploaded_by=admin.id,
    )
    db.add(textbook)
    db.commit()
    db.refresh(textbook)
    return textbook


@router.get("/folders/{folder_id}/textbooks", response_model=list[TextbookOut])
def list_textbooks_in_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folder = db.query(TextbookFolder).filter(TextbookFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return (
        db.query(Textbook)
        .filter(Textbook.folder_id == folder_id)
        .order_by(Textbook.title.asc())
        .all()
    )


@router.get("/{textbook_id}/download")
def download_textbook(
    textbook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    return Response(
        content=textbook.file_data,
        media_type=textbook.content_type,
        headers={"Content-Disposition": f'inline; filename="{textbook.filename}"'},
    )


@router.delete("/{textbook_id}", status_code=204)
def delete_textbook(
    textbook_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    db.delete(textbook)
    db.commit()
    return None


@router.post("/{textbook_id}/generate-questions", response_model=list[PendingQuestionOut])
def generate_questions_from_textbook(
    textbook_id: uuid.UUID,
    payload: GenerateFromTextbookRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-only, same as every other AI-generation endpoint. Extracts text
    from the already-uploaded document (e.g. real past questions, with
    school permission) and generates NEW original questions inspired by it —
    never copying the original wording verbatim. Lands in the same pending
    review queue as everything else in the admin content pipeline; nothing
    reaches students until explicitly approved."""
    _check_tutor_available(db, admin.id)

    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    extracted_text = extract_text_from_upload(textbook.filename, textbook.file_data)

    system_prompt = (
        "You write NMCN (Nursing and Midwifery Council of Nigeria) exam-style practice questions "
        f"for the topic '{topic.name}'.\n\n"
        "The source material below contains PAST EXAM QUESTIONS the school has given permission "
        "to use as a basis for new practice content. Do NOT copy any question verbatim. Instead, "
        "write NEW original questions that test the same underlying concepts and difficulty level, "
        "in your own wording, inspired by the patterns you see.\n\n"
        "Respond with ONLY valid JSON, nothing else, using EXACTLY this structure "
        "(a single object with a questions key, not a bare array):\n"
        '{"questions": [{"stem": "...", "difficulty": "easy|medium|hard", "explanation": "...", '
        '"options": [{"text": "...", "is_correct": true|false}, ...]}]}\n\n'
        "Each question must have exactly 4 options with exactly ONE marked is_correct: true. "
        f"Generate up to {payload.count} questions."
    )

    reply_text = _call_gemini(
        system_prompt,
        f"Source material:\n\n{extracted_text}",
        response_mime_type="application/json",
        max_output_tokens=8000,
    )

    try:
        parsed, _ = json.JSONDecoder().raw_decode((reply_text or "{}").strip())
        raw_questions = parsed if isinstance(parsed, list) else parsed["questions"]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"The AI didn't return usable questions - try again. ({exc})")

    created = []
    for raw_q in raw_questions:
        try:
            options = raw_q["options"]
            correct_count = sum(1 for o in options if o.get("is_correct"))
            if len(options) < 2 or correct_count != 1:
                continue
            pending = PendingQuestion(
                source_document_id=None,
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
