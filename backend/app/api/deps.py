import uuid
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_access_token
from app.core.time import utcnow
from app.db.session import get_db
from app.models.user import User
from app.models.user_session import UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# How stale last_active_at has to be before a request bothers updating it --
# avoids a write on literally every authenticated request just to bump a
# "last active" timestamp a few seconds.
LAST_ACTIVE_UPDATE_INTERVAL = timedelta(minutes=5)


def get_current_session(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserSession:
    """Resolves a request's token to its UserSession row -- not just a JWT
    decode. A token whose session was deleted (logged out from another
    device, including via Settings) is rejected here immediately, on its
    very next request, rather than only failing once the JWT's own exp is
    reached."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    session_id = payload.get("jti")
    if session_id is None:
        raise credentials_exception

    try:
        session = (
            db.query(UserSession)
            .options(joinedload(UserSession.user))
            .filter(UserSession.id == uuid.UUID(session_id), UserSession.expires_at > utcnow())
            .first()
        )
    except ValueError:
        raise credentials_exception

    if session is None or session.user is None:
        raise credentials_exception

    now = utcnow()
    if now - session.last_active_at > LAST_ACTIVE_UPDATE_INTERVAL:
        session.last_active_at = now
        db.commit()

    return session


def get_current_user(session: UserSession = Depends(get_current_session)) -> User:
    return session.user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Content-management endpoints (subjects/topics/questions writes, and any
    read that would expose answer keys) require this instead of get_current_user."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
