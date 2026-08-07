from datetime import timedelta

from app.core.time import utcnow
from app.models.email_verification_token import EmailVerificationToken
from app.models.user import User


def _get_verification_token(db_session, email: str) -> str:
    user = db_session.query(User).filter(User.email == email).first()
    token_row = (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == user.id)
        .order_by(EmailVerificationToken.created_at.desc())
        .first()
    )
    return token_row.token


def test_new_signup_is_not_verified(client):
    response = client.post(
        "/auth/signup", json={"email": "unverified@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json()["email_verified"] is False


def test_unverified_user_cannot_login(client):
    client.post("/auth/signup", json={"email": "blocked@example.com", "password": "password123"})
    response = client.post(
        "/auth/login", data={"username": "blocked@example.com", "password": "password123"}
    )
    assert response.status_code == 403
    assert "verify your email" in response.json()["detail"].lower()


def test_verify_email_with_valid_token_allows_login(client, db_session):
    email = "verify-me@example.com"
    client.post("/auth/signup", json={"email": email, "password": "password123"})
    token = _get_verification_token(db_session, email)

    verify_response = client.post("/auth/verify-email", json={"token": token})
    assert verify_response.status_code == 200

    login_response = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert login_response.status_code == 200


def test_verify_email_token_cannot_be_reused(client, db_session):
    email = "reuse-verify@example.com"
    client.post("/auth/signup", json={"email": email, "password": "password123"})
    token = _get_verification_token(db_session, email)

    first = client.post("/auth/verify-email", json={"token": token})
    assert first.status_code == 200

    second = client.post("/auth/verify-email", json={"token": token})
    assert second.status_code == 400


def test_verify_email_rejects_expired_token(client, db_session):
    email = "expired-verify@example.com"
    client.post("/auth/signup", json={"email": email, "password": "password123"})

    user = db_session.query(User).filter(User.email == email).first()
    token_row = (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == user.id)
        .first()
    )
    token_row.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()

    response = client.post("/auth/verify-email", json={"token": token_row.token})
    assert response.status_code == 400


def test_verify_email_rejects_unknown_token(client):
    response = client.post("/auth/verify-email", json={"token": "not-a-real-token"})
    assert response.status_code == 400


def test_resend_verification_issues_a_new_working_token(client, db_session):
    email = "resend-me@example.com"
    client.post("/auth/signup", json={"email": email, "password": "password123"})
    old_token = _get_verification_token(db_session, email)

    resend_response = client.post("/auth/resend-verification", json={"email": email})
    assert resend_response.status_code == 200

    new_token = _get_verification_token(db_session, email)
    assert new_token != old_token

    verify_response = client.post("/auth/verify-email", json={"token": new_token})
    assert verify_response.status_code == 200


def test_resend_verification_does_not_leak_whether_email_exists(client):
    registered = client.post("/auth/resend-verification", json={"email": "someone@example.com"})
    unregistered = client.post(
        "/auth/resend-verification", json={"email": "nobody-here@example.com"}
    )
    assert registered.status_code == 200
    assert unregistered.status_code == 200
    assert registered.json() == unregistered.json()


def test_resend_verification_does_nothing_for_already_verified_user(client, db_session, verify_user):
    email = "already-verified@example.com"
    client.post("/auth/signup", json={"email": email, "password": "password123"})
    verify_user(email)

    count_before = db_session.query(EmailVerificationToken).count()
    client.post("/auth/resend-verification", json={"email": email})
    count_after = db_session.query(EmailVerificationToken).count()
    assert count_after == count_before
