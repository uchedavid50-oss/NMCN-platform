"""Shared free-tier trial gating, used by every feature that caps free
students at a fixed number of attempts before requiring a subscription
(CBT exam, mock exam, practice, flashcards, speed round, past-questions,
clinical cases). Admins and active subscribers are always unlimited."""
from fastapi import HTTPException

from app.models.user import User

FREE_TRIAL_LIMIT = 2


def is_unlimited(user: User) -> bool:
    return user.role == "admin" or user.subscription_status == "active"


def enforce_free_trial(user: User, existing_count: int, feature_label: str) -> None:
    """Raises 403 once a free (non-admin, non-subscribed) user has already
    used existing_count >= FREE_TRIAL_LIMIT attempts at the calling feature.
    The caller is responsible for computing existing_count from whatever
    model tracks that feature's attempts."""
    if is_unlimited(user):
        return
    if existing_count >= FREE_TRIAL_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Free tier is limited to {FREE_TRIAL_LIMIT} {feature_label}. "
                "Subscribe via POST /payments/initialize to continue."
            ),
        )
