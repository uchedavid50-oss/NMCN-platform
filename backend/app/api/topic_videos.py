import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin, get_current_user
from app.core.time import utcnow
from app.db.session import get_db
from app.models.topic import Topic
from app.models.topic_video import TopicVideo
from app.models.user import User
from app.schemas.topic_videos import TopicVideoOut, SetTopicVideoRequest

router = APIRouter(prefix="/topic-videos", tags=["topic-videos"])


@router.get("/{topic_id}", response_model=TopicVideoOut)
def get_topic_video(
    topic_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = db.query(TopicVideo).filter(TopicVideo.topic_id == topic_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="No demonstration video yet for this topic.")
    return video


@router.put("/{topic_id}", response_model=TopicVideoOut)
def set_topic_video(
    topic_id: uuid.UUID,
    payload: SetTopicVideoRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    video = db.query(TopicVideo).filter(TopicVideo.topic_id == topic_id).first()
    if video:
        video.youtube_url = payload.youtube_url
        video.updated_at = utcnow()
    else:
        video = TopicVideo(topic_id=topic_id, youtube_url=payload.youtube_url)
        db.add(video)

    db.commit()
    db.refresh(video)
    return video
