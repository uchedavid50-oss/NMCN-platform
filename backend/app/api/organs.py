import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin, get_current_user
from app.core.time import utcnow
from app.db.session import get_db
from app.models.organ import Organ
from app.models.organ_video import OrganVideo
from app.models.user import User
from app.schemas.organs import OrganOut, OrganVideoOut, SetOrganVideoRequest

router = APIRouter(prefix="/organs", tags=["organs"])


@router.get("", response_model=list[OrganOut])
def list_organs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Organ).order_by(Organ.name).all()


@router.get("/{organ_id}/video", response_model=OrganVideoOut)
def get_organ_video(
    organ_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = db.query(OrganVideo).filter(OrganVideo.organ_id == organ_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="No video yet for this organ.")
    return video


@router.put("/{organ_id}/video", response_model=OrganVideoOut)
def set_organ_video(
    organ_id: uuid.UUID,
    payload: SetOrganVideoRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    organ = db.query(Organ).filter(Organ.id == organ_id).first()
    if not organ:
        raise HTTPException(status_code=404, detail="Organ not found")

    video = db.query(OrganVideo).filter(OrganVideo.organ_id == organ_id).first()
    if video:
        video.youtube_url = payload.youtube_url
        video.updated_at = utcnow()
    else:
        video = OrganVideo(organ_id=organ_id, youtube_url=payload.youtube_url)
        db.add(video)

    db.commit()
    db.refresh(video)
    return video
