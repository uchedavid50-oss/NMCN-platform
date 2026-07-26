import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin, get_current_user
from app.api.tutor import _call_gemini, _check_tutor_available
from app.core.time import utcnow
from app.db.session import get_db
from app.models.topic import Topic
from app.models.topic_note import TopicNote
from app.models.user import User
from app.schemas.topic_notes import TopicNoteOut, GenerateNoteRequest

router = APIRouter(prefix="/topic-notes", tags=["topic-notes"])

EXAM_FRAMING = {
    "NMCN": "the NMCN (Nursing and Midwifery Council of Nigeria) Professional Qualifying Examination",
    "NCLEX": "the NCLEX (National Council Licensure Examination) for nursing licensure",
}


@router.get("/{topic_id}", response_model=TopicNoteOut)
def get_topic_note(
    topic_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(TopicNote).filter(TopicNote.topic_id == topic_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="No study note yet for this topic.")
    return note


@router.post("/generate", response_model=TopicNoteOut)
def generate_topic_note(
    payload: GenerateNoteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _check_tutor_available(db, admin.id)

    topic = (
        db.query(Topic)
        .options(joinedload(Topic.subject))
        .filter(Topic.id == payload.topic_id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    exam_type = topic.subject.exam_type if topic.subject else "NMCN"
    exam_framing = EXAM_FRAMING.get(exam_type, EXAM_FRAMING["NMCN"])

    system_prompt = (
        f"You write comprehensive study notes for a nursing student preparing for "
        f"{exam_framing}, on the topic '{topic.name}' (subject: "
        f"{topic.subject.name if topic.subject else 'General'}).\n\n"
        "Write a thorough, well-organized study note covering the key concepts, "
        "definitions, clinical relevance, and any important nursing considerations "
        "for this topic. Use Markdown formatting: headings, bullet points, and bold "
        "for key terms. Where a diagram would genuinely help understanding (e.g. a "
        "process, cycle, anatomical relationship, or classification), include ONE "
        "Mermaid diagram in a ```mermaid code block using flowchart or graph syntax. "
        "Do not overuse diagrams -- only include one if it adds real value. "
        "Respond with ONLY the markdown content, no preamble or meta-commentary."
    )

    reply_text = _call_gemini(
        system_prompt,
        f"Topic: {topic.name}",
        max_output_tokens=4000,
    )

    if not reply_text or not reply_text.strip():
        raise HTTPException(status_code=502, detail="The AI didn't return a usable note - try again.")

    note = db.query(TopicNote).filter(TopicNote.topic_id == topic.id).first()
    if note:
        note.content = reply_text.strip()
        note.updated_at = utcnow()
    else:
        note = TopicNote(topic_id=topic.id, content=reply_text.strip())
        db.add(note)

    db.commit()
    db.refresh(note)
    return note