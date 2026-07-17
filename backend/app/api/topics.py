import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicOut, TopicUpdate

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    topic = Topic(subject_id=payload.subject_id, name=payload.name)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("", response_model=List[TopicOut])
def list_topics(subject_id: Optional[uuid.UUID] = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(Topic)
    if subject_id:
        query = query.filter(Topic.subject_id == subject_id)
    return query.order_by(Topic.name).all()


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: uuid.UUID, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.put("/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: uuid.UUID,
    payload: TopicUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.name = payload.name
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)  # cascades to questions -> options
    db.commit()
    return None
