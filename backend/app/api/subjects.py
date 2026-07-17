import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectOut, SubjectUpdate

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    existing = db.query(Subject).filter(Subject.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject already exists")
    subject = Subject(name=payload.name)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("", response_model=List[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).order_by(Subject.name).all()


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: uuid.UUID, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject.name = payload.name
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)  # cascades to topics -> questions -> options
    db.commit()
    return None
