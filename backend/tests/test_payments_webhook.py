import hashlib
import hmac
import json

from app.core.config import settings
from app.models.subscription import Subscription


FAKE_SECRET = "sk_test_fake_key_for_testing_only"


def _sign(body: bytes, secret: str = FAKE_SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()


def test_webhook_rejects_missing_signature(client, monkeypatch):
    monkeypatch.setattr(settings, "paystack_secret_key", FAKE_SECRET)
    payload = {"event": "charge.success", "data": {"reference": "nmcn_test123"}}
    response = client.post("/payments/webhook", content=json.dumps(payload))
    assert response.status_code == 401


def test_webhook_rejects_wrong_signature(client, monkeypatch):
    monkeypatch.setattr(settings, "paystack_secret_key", FAKE_SECRET)
    payload = {"event": "charge.success", "data": {"reference": "nmcn_test123"}}
    body = json.dumps(payload).encode()
    response = client.post(
        "/payments/webhook",
        content=body,
        headers={"x-paystack-signature": "not_the_real_signature"},
    )
    assert response.status_code == 401


def test_webhook_activates_subscription_on_valid_signature(
    client, monkeypatch, make_user, db_session
):
    monkeypatch.setattr(settings, "paystack_secret_key", FAKE_SECRET)
    user, _ = make_user(subscription_status="free")

    subscription = Subscription(
        user_id=user.id,
        plan="premium_monthly",
        status="pending",
        provider="paystack",
        reference="nmcn_test_reference_123",
        amount_kobo=500000,
        currency="NGN",
    )
    db_session.add(subscription)
    db_session.commit()

    payload = {"event": "charge.success", "data": {"reference": "nmcn_test_reference_123"}}
    body = json.dumps(payload).encode()
    signature = _sign(body)

    response = client.post(
        "/payments/webhook", content=body, headers={"x-paystack-signature": signature}
    )
    assert response.status_code == 200
    assert response.json() == {"received": True}

    db_session.refresh(subscription)
    db_session.refresh(user)
    assert subscription.status == "active"
    assert user.subscription_status == "active"
    assert subscription.expires_at is not None


def test_webhook_ignores_unknown_reference_gracefully(client, monkeypatch):
    """Paystack expects a 200 even for events we don't recognize or can't match —
    otherwise it treats it as a failed delivery and retries indefinitely."""
    monkeypatch.setattr(settings, "paystack_secret_key", FAKE_SECRET)
    payload = {"event": "charge.success", "data": {"reference": "nmcn_does_not_exist"}}
    body = json.dumps(payload).encode()
    signature = _sign(body)

    response = client.post(
        "/payments/webhook", content=body, headers={"x-paystack-signature": signature}
    )
    assert response.status_code == 200
