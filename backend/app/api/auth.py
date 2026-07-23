from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.core.time import utcnow
from app.core.totp import generate_totp_secret, get_provisioning_uri, verify_totp_code
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    Token,
    TwoFactorCodeRequest,
    TwoFactorSetupResponse,
    UserOut,
    UserSignup,
)

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _register_failed_attempt(user: User, db: Session):
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
    db.commit()


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses "username" as the field name; we treat it as the email.
    user = db.query(User).filter(User.email == form_data.username).first()

    if user and user.locked_until and user.locked_until > utcnow():
        minutes_left = max(1, int((user.locked_until - utcnow()).total_seconds() // 60) + 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {minutes_left} minute(s).",
        )

    if not user or not verify_password(form_data.password, user.password_hash):
        if user:
            _register_failed_attempt(user, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.totp_enabled:
        if not totp_code:
            # Distinct 400, not 401 -- this tells the frontend "password was
            # right, now ask the user for their authenticator code" rather
            # than "wrong credentials, try again from scratch".
            raise HTTPException(status_code=400, detail="2FA code required")
        if not verify_totp_code(user.totp_secret, totp_code):
            _register_failed_attempt(user, db)
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_two_factor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a new secret but does NOT enable 2FA yet -- enabling only
    happens after /2fa/verify confirms the user actually has it working in
    their authenticator app, so no one can lock themselves out by mistake."""
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    db.commit()
    return TwoFactorSetupResponse(
        secret=secret,
        provisioning_uri=get_provisioning_uri(secret, current_user.email),
    )


@router.post("/2fa/verify", response_model=UserOut)
def verify_two_factor_setup(
    payload: TwoFactorCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Call /auth/2fa/setup first")
    if not verify_totp_code(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    current_user.totp_enabled = True
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/2fa/disable", response_model=UserOut)
def disable_two_factor(
    payload: TwoFactorCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Requires a currently-valid code to disable, not just an active session
    -- a stolen JWT alone should not be enough to turn off 2FA protection."""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not verify_totp_code(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    db.refresh(current_user)
    return current_user
