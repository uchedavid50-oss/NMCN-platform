import hashlib
import hmac
import uuid
from datetime import timedelta

from app.core.time import utcnow

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.payment import (
    InitializePaymentRequest,
    InitializePaymentResponse,
    SubscriptionStatusOut,
)

router = APIRouter(prefix="/payments", tags=["payments"])

# Fixed plan catalogue for MVP — a real "plans" table/admin UI can come later if needed.
PLAN_PRICES_KOBO = {
    "premium_monthly": 500000,  # ₦5,000
}
PLAN_DURATION_DAYS = {
    "premium_monthly": 30,
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
        if subscription and subscription.status != "active":
            now = utcnow()
            duration_days = PLAN_DURATION_DAYS.get(subscription.plan, 30)

            subscription.status = "active"
            subscription.activated_at = now
            subscription.expires_at = now + timedelta(days=duration_days)

            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.subscription_status = "active"

            db.commit()

    # Paystack expects a 200 regardless of whether we recognized the event,
    # otherwise it will keep retrying the same webhook.
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
