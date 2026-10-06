import hashlib
import hmac
import uuid

from app.core.time import utcnow

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import PREMIUM_LIFETIME_PRICE_KOBO, settings
from app.db.session import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.payment import (
    InitializePaymentRequest,
    InitializePaymentResponse,
    MarkPaidRequest,
    SubscriptionStatusOut,
    VerifyPaymentResponse,
)
from app.services.email import send_admin_payment_notification

router = APIRouter(prefix="/payments", tags=["payments"])

# One-time payment, lifetime access -- no recurring charge, no expiry.
# Kept as a dict (not a single constant) so a second tier could be added
# later without changing the endpoint shape.
PLAN_PRICES_KOBO = {
    "premium_lifetime": PREMIUM_LIFETIME_PRICE_KOBO,  # one-time
}


@router.post("/initialize", response_model=InitializePaymentResponse)
def initialize_payment(
    payload: InitializePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.plan not in PLAN_PRICES_KOBO:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{payload.plan}'")

    if not settings.paystack_secret_key:
        raise HTTPException(
            status_code=500,
            detail="PAYSTACK_SECRET_KEY is not configured on the server. "
            "Set it in backend/.env before initializing payments.",
        )

    amount_kobo = PLAN_PRICES_KOBO[payload.plan]
    reference = f"nmcn_{uuid.uuid4().hex}"

    subscription = Subscription(
        user_id=current_user.id,
        plan=payload.plan,
        status="pending",
        provider="paystack",
        reference=reference,
        amount_kobo=amount_kobo,
        currency="NGN",
    )
    db.add(subscription)
    db.commit()

    try:
        response = httpx.post(
            f"{settings.paystack_base_url}/transaction/initialize",
            headers={
                "Authorization": f"Bearer {settings.paystack_secret_key}",
                "Content-Type": "application/json",
            },
            json={
                "email": current_user.email,
                "amount": amount_kobo,
                "reference": reference,
                "callback_url": settings.frontend_callback_url,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        subscription.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Paystack initialization failed: {exc}")

    if not data.get("status"):
        subscription.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Paystack rejected the request: {data.get('message')}")

    return InitializePaymentResponse(
        authorization_url=data["data"]["authorization_url"],
        reference=reference,
    )


def _verify_paystack_signature(raw_body: bytes, signature_header: str) -> bool:
    if not settings.paystack_secret_key or not signature_header:
        return False
    expected = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _activate_subscription(db: Session, subscription: Subscription) -> bool:
    """Marks a subscription active and its user paid. Shared by the webhook,
    the callback-page verify endpoint, and the admin manual override, and
    idempotent across all three: the row is locked and re-read first, so two
    concurrent callers (webhook + page refresh) serialize and only the first
    one does any work. Returns True only if this call performed the
    activation."""
    locked = (
        db.query(Subscription)
        .filter(Subscription.id == subscription.id)
        .with_for_update()
        .one()
    )
    if locked.status == "active":
        db.commit()  # release the row lock
        return False

    locked.status = "active"
    locked.activated_at = utcnow()
    # One-time payment, lifetime access -- deliberately no expires_at.
    # A student who has paid once should never be silently downgraded.
    locked.expires_at = None

    user = db.query(User).filter(User.id == locked.user_id).first()
    if user:
        user.subscription_status = "active"
    db.commit()

    if user:
        try:
            send_admin_payment_notification(user.email, locked.amount_kobo, locked.plan)
        except Exception as exc:
            # Never let a notification-email failure block activation --
            # Paystack retries webhooks that don't 200.
            print(f"[payments] Failed to send admin notification for {user.email}: {exc}")
    return True


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not _verify_paystack_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")
    data = payload.get("data", {})
    reference = data.get("reference")

    if event == "charge.success" and reference:
        subscription = db.query(Subscription).filter(Subscription.reference == reference).first()
        if subscription:
            _activate_subscription(db, subscription)

    return {"received": True}


@router.get("/subscription", response_model=SubscriptionStatusOut)
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    return SubscriptionStatusOut(
        plan=latest.plan if latest else None,
        status=current_user.subscription_status,
        expires_at=latest.expires_at if latest else None,
    )


@router.get("/verify/{reference}", response_model=VerifyPaymentResponse)
def verify_payment(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Called by the payment callback page. Asks Paystack directly whether
    the transaction succeeded (never trusts the client) and activates the
    account immediately, so access doesn't depend on the webhook arriving
    first. Safe to call repeatedly: a refresh or a webhook that already
    landed is a no-op."""
    # Scoped to the caller so one user can't probe or activate another's reference.
    subscription = (
        db.query(Subscription)
        .filter(Subscription.reference == reference, Subscription.user_id == current_user.id)
        .first()
    )
    if not subscription:
        raise HTTPException(status_code=404, detail="Unknown payment reference")

    if subscription.status == "active":
        return VerifyPaymentResponse(status="active", subscription_status=current_user.subscription_status)

    if not settings.paystack_secret_key:
        raise HTTPException(status_code=500, detail="PAYSTACK_SECRET_KEY is not configured on the server.")

    try:
        response = httpx.get(
            f"{settings.paystack_base_url}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            timeout=15.0,
        )
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Paystack verification failed: {exc}")

    data = body.get("data") or {}
    if (
        not body.get("status")
        or data.get("status") != "success"
        or data.get("reference") != reference
        or data.get("amount") != subscription.amount_kobo
        or data.get("currency", subscription.currency) != subscription.currency
    ):
        # Not (yet) successful -- the page keeps polling; abandoned/failed
        # transactions simply stay pending.
        return VerifyPaymentResponse(status=data.get("status") or "pending", subscription_status=current_user.subscription_status)

    _activate_subscription(db, subscription)
    db.refresh(current_user)
    return VerifyPaymentResponse(status="active", subscription_status=current_user.subscription_status)


@router.post("/admin/mark-paid", response_model=SubscriptionStatusOut)
def admin_mark_paid(
    payload: MarkPaidRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Support override: grants lifetime access without a Paystack payment
    (e.g. a bank transfer, or a webhook that never arrived). Records a
    zero-amount 'manual' subscription so the grant is traceable to the
    admin who made it. Idempotent -- an already-paid user is left alone."""
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user with that email")

    if user.subscription_status != "active":
        subscription = Subscription(
            user_id=user.id,
            plan="premium_lifetime",
            status="pending",
            provider="manual",
            reference=f"manual_{admin.id.hex[:8]}_{uuid.uuid4().hex}",
            amount_kobo=0,
            currency="NGN",
        )
        db.add(subscription)
        db.commit()
        _activate_subscription(db, subscription)
        db.refresh(user)

    return SubscriptionStatusOut(plan="premium_lifetime", status=user.subscription_status, expires_at=None)
