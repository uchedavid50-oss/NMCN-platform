import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.api.tutor import _call_gemini, _check_tutor_available
from app.db.session import get_db
from app.models.dictionary_entry import DictionaryEntry
from app.models.user import User
from app.schemas.dictionary import DictionaryEntryOut, DictionarySearchRequest, DictionaryVerifyRequest

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


@router.post("/search", response_model=DictionaryEntryOut)
def search_dictionary(
    payload: DictionarySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    term_normalized = payload.term.strip()

    existing = (
        db.query(DictionaryEntry)
        .filter(func.lower(DictionaryEntry.term) == term_normalized.lower())
        .first()
    )
    if existing:
        return existing

    _check_tutor_available(db, current_user.id)

    system_prompt = (
        "You are a nursing/medical dictionary. Given a term, provide a clear, accurate, concise "
        "definition (2-4 sentences) suitable for a nursing student preparing for a professional "
        "licensing examination. Plain text only, no markdown formatting, no preamble like "
        "'Definition:' - just the definition itself."
    )
    definition = _call_gemini(system_prompt, term_normalized, max_output_tokens=300)

    entry = DictionaryEntry(term=term_normalized, definition=definition, is_verified=False)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=list[DictionaryEntryOut])
def list_dictionary(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DictionaryEntry)
    if q:
        query = query.filter(DictionaryEntry.term.ilike(f"%{q}%"))
    return query.order_by(DictionaryEntry.term.asc()).limit(100).all()


@router.patch("/{entry_id}/verify", response_model=DictionaryEntryOut)
def verify_dictionary_entry(
    entry_id: uuid.UUID,
    payload: DictionaryVerifyRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    entry = db.query(DictionaryEntry).filter(DictionaryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if payload.definition:
        entry.definition = payload.definition
    entry.is_verified = True
    db.commit()
    db.refresh(entry)
    return entry
