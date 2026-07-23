from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.focus_session import FocusSession
from app.models.user import User
from app.schemas.focus import FocusSessionCompleteRequest, FocusSessionCompleteResponse
from app.services.streaks import compute_streak

router = APIRouter(prefix="/focus", tags=["focus"])


@router.post("/complete", response_model=FocusSessionCompleteResponse)
def complete_focus_session(
    payload: FocusSessionCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.add(FocusSession(user_id=current_user.id, duration_minutes=payload.duration_minutes))
    db.commit()

    total_sessions = db.query(FocusSession).filter(FocusSession.user_id == current_user.id).count()
    all_sessions = db.query(FocusSession.duration_minutes).filter(
        FocusSession.user_id == current_user.id
    ).all()
    total_minutes = sum(m for (m,) in all_sessions)

    streak, _ = compute_streak(db, current_user.id)

    return FocusSessionCompleteResponse(
        total_sessions=total_sessions,
        total_minutes=total_minutes,
        current_streak=streak,
    )
