"""Free tier is gone: content endpoints require a paid (or admin) account,
while auth and payment endpoints stay reachable so an unpaid user can still
sign in, pay, and log out."""
import hashlib
import hmac
import json

import pytest

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User

# One representative GET per content router (all routers that serve content
# to students; admin-only routers are covered by their own tests).
CONTENT_GETS = [
    "/subjects",
    "/topics",
    "/past-questions/count",
    "/past-questions/practice",
    "/flashcards?topic_id=00000000-0000-0000-0000-000000000000",
    "/notes",
    "/analytics/overview",
    "/analytics/history",
    "/games/streak",
    "/games/leaderboard",
    "/games/speed-round/start",
    "/achievements/badges",
    "/clinical-cases",
    "/dictionary",
    "/mnemonics",
    "/equipment",
    "/organs",
    "/textbooks/folders",
    "/entrance-exam/questions?subject=Anatomy",
    "/cgpa/summary",
]
CONTENT_POSTS = [
    ("/practice/start", {"topic_id": "00000000-0000-0000-0000-000000000000"}),
    ("/mock/start", {"topic_id": "00000000-0000-0000-0000-000000000000"}),
    ("/cbt-exam/start", {}),
    ("/tutor/ask", {"question": "hi"}),
    ("/focus/complete", {"minutes": 25}),
]


def _assert_payment_required(response):
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PAYMENT_REQUIRED"


@pytest.mark.parametrize("path", CONTENT_GETS)
def test_free_user_gets_403_on_content_get(client, free_headers, path):
    _assert_payment_required(client.get(path, headers=free_headers))


@pytest.mark.parametrize("path,body", CONTENT_POSTS)
def test_free_user_gets_403_on_content_post(client, free_headers, path, body):
    _assert_payment_required(client.post(path, json=body, headers=free_headers))


def test_expired_user_gets_403(client, make_user):
    _, token = make_user(subscription_status="expired")
    _assert_payment_required(client.get("/subjects", headers={"Authorization": f"Bearer {token}"}))


@pytest.mark.parametrize("path", ["/subjects", "/topics", "/past-questions/count"])
def test_anonymous_still_rejected(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ["/subjects", "/topics", "/past-questions/count", "/notes", "/analytics/overview", "/games/streak"])
def test_paid_user_gets_200(client, auth_headers, path):
    assert client.get(path, headers=auth_headers).status_code == 200


@pytest.mark.parametrize("path", ["/subjects", "/topics", "/past-questions/count", "/notes", "/analytics/overview", "/games/streak"])
def test_admin_gets_200(client, admin_headers, path):
    assert client.get(path, headers=admin_headers).status_code == 200


def test_free_user_can_still_reach_auth_and_payment_endpoints(client, free_headers, monkeypatch):
    assert client.get("/auth/me", headers=free_headers).status_code == 200
    assert client.get("/auth/sessions", headers=free_headers).status_code == 200
    assert client.get("/payments/subscription", headers=free_headers).status_code == 200
    # Unknown reference -> 404 from our own logic, i.e. the endpoint was reached (not 403).
    assert client.get("/payments/verify/nmcn_nope", headers=free_headers).status_code == 404
    # Reaches the "not configured" branch rather than being blocked by the paywall.
    monkeypatch.setattr(settings, "paystack_secret_key", "")
    response = client.post("/payments/initialize", json={"plan": "premium_lifetime"}, headers=free_headers)
    assert response.status_code == 500
    assert client.get("/public/stats").status_code == 200


def test_webhook_is_not_paywalled(client):
    # No auth header at all: rejected by signature check (401), never by the paywall.
    response = client.post("/payments/webhook", content=b"{}")
    assert response.status_code == 401


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self._body


def _pending_subscription(db_session, user, reference="nmcn_verify_ref"):
    sub = Subscription(
        user_id=user.id, plan="premium_lifetime", status="pending", provider="paystack",
        reference=reference, amount_kobo=300000, currency="NGN",
    )
    db_session.add(sub)
    db_session.commit()
    return sub


def test_verify_activates_user_and_is_idempotent(client, make_user, db_session, monkeypatch):
    monkeypatch.setattr(settings, "paystack_secret_key", "sk_test_fake")
    user, token = make_user(subscription_status="free")
    headers = {"Authorization": f"Bearer {token}"}
    _pending_subscription(db_session, user)

    calls = {"paystack": 0, "emails": 0}

    def fake_get(url, **kwargs):
        calls["paystack"] += 1
        return _FakeResponse({"status": True, "data": {
            "status": "success", "reference": "nmcn_verify_ref", "amount": 300000, "currency": "NGN"}})

    monkeypatch.setattr("app.api.payments.httpx.get", fake_get)
    monkeypatch.setattr(
        "app.api.payments.send_admin_payment_notification",
        lambda *a, **k: calls.__setitem__("emails", calls["emails"] + 1),
    )

    first = client.get("/payments/verify/nmcn_verify_ref", headers=headers)
    assert first.status_code == 200 and first.json()["subscription_status"] == "active"
    db_session.refresh(user)
    assert user.subscription_status == "active"
    # Immediately has access to content.
    assert client.get("/subjects", headers=headers).status_code == 200

    # Page refresh + duplicate webhook: no second Paystack call, no second email.
    assert client.get("/payments/verify/nmcn_verify_ref", headers=headers).status_code == 200
    body = json.dumps({"event": "charge.success", "data": {"reference": "nmcn_verify_ref"}}).encode()
    sig = hmac.new(b"sk_test_fake", body, hashlib.sha512).hexdigest()
    assert client.post("/payments/webhook", content=body, headers={"x-paystack-signature": sig}).status_code == 200
    assert calls == {"paystack": 1, "emails": 1}


def test_verify_does_not_activate_on_failed_or_mismatched_transaction(client, make_user, db_session, monkeypatch):
    monkeypatch.setattr(settings, "paystack_secret_key", "sk_test_fake")
    user, token = make_user(subscription_status="free")
    headers = {"Authorization": f"Bearer {token}"}
    _pending_subscription(db_session, user)

    for data in (
        {"status": "abandoned", "reference": "nmcn_verify_ref", "amount": 300000, "currency": "NGN"},
        {"status": "success", "reference": "nmcn_verify_ref", "amount": 100, "currency": "NGN"},
    ):
        monkeypatch.setattr("app.api.payments.httpx.get", lambda *a, _d=data, **k: _FakeResponse({"status": True, "data": _d}))
        response = client.get("/payments/verify/nmcn_verify_ref", headers=headers)
        assert response.status_code == 200
        assert response.json()["subscription_status"] == "free"
    db_session.refresh(user)
    assert user.subscription_status == "free"


def test_verify_rejects_another_users_reference(client, make_user, db_session):
    owner, _ = make_user()
    _, other_token = make_user()
    _pending_subscription(db_session, owner)
    response = client.get("/payments/verify/nmcn_verify_ref", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 404


def test_admin_mark_paid(client, make_user, admin_headers, db_session):
    user, token = make_user(subscription_status="free")
    response = client.post("/payments/admin/mark-paid", json={"email": user.email.upper()}, headers=admin_headers)
    assert response.status_code == 200
    db_session.refresh(user)
    assert user.subscription_status == "active"
    assert client.get("/subjects", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    # Idempotent: second call creates no extra subscription row.
    client.post("/payments/admin/mark-paid", json={"email": user.email}, headers=admin_headers)
    assert db_session.query(Subscription).filter(Subscription.user_id == user.id).count() == 1


def test_admin_mark_paid_is_admin_only(client, free_headers, auth_headers):
    body = {"email": "x@example.com"}
    assert client.post("/payments/admin/mark-paid", json=body, headers=free_headers).status_code == 403
    assert client.post("/payments/admin/mark-paid", json=body, headers=auth_headers).status_code == 403
