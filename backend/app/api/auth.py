import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.core.time import utcnow
from app.core.totp import generate_totp_secret, get_provisioning_uri, verify_totp_code
from app.db.session import get_db
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    TwoFactorCodeRequest,
    TwoFactorSetupResponse,
    UserOut,
    UserSignup,
)
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1


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
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not verify_totp_code(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Always returns the same generic message whether or not the email is
    registered -- this prevents someone from using this endpoint to discover
    which email addresses have accounts on the platform."""
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        token = secrets.token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=utcnow() + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS),
            )
        )
        db.commit()
        reset_link = f"{settings.frontend_url}/reset-password?token={token}"
        try:
            send_password_reset_email(user.email, reset_link)
        except Exception:
            # Don't leak email-delivery failures to the caller either -- same
            # reasoning as not leaking whether the account exists.
            pass

    return {"message": "If that email is registered, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset = db.query(PasswordResetToken).filter(PasswordResetToken.token == payload.token).first()
    if not reset or reset.used_at is not None or reset.expires_at < utcnow():
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    user = db.query(User).filter(User.id == reset.user_id).first()
    user.password_hash = hash_password(payload.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    reset.used_at = utcnow()
    db.commit()
    return {"message": "Password has been reset successfully."}
