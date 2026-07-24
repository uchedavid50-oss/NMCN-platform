import app.api.auth as auth_module


def _noop_email(*args, **kwargs):
    pass


def test_forgot_password_generic_message_for_unknown_email(client, monkeypatch):
    monkeypatch.setattr(auth_module, "send_password_reset_email", _noop_email)
    response = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert response.status_code == 200
    assert "if that email is registered" in response.json()["message"].lower()


def test_forgot_password_generic_message_for_known_email(client, monkeypatch):
    monkeypatch.setattr(auth_module, "send_password_reset_email", _noop_email)
    client.post("/auth/signup", json={"email": "reset-flow@example.com", "password": "oldpass1"})

    response = client.post("/auth/forgot-password", json={"email": "reset-flow@example.com"})
    assert response.status_code == 200
    assert "if that email is registered" in response.json()["message"].lower()


def test_forgot_password_survives_email_sending_failure(client, monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("Resend API down")

    monkeypatch.setattr(auth_module, "send_password_reset_email", _raise)
    client.post("/auth/signup", json={"email": "email-fails@example.com", "password": "oldpass1"})

    response = client.post("/auth/forgot-password", json={"email": "email-fails@example.com"})
    assert response.status_code == 200


def _get_reset_token_for_email(db_session, email):
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    user = db_session.query(User).filter(User.email == email).first()
    token_row = (
        db_session.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user.id)
        .order_by(PasswordResetToken.created_at.desc())
        .first()
    )
    return token_row.token


def test_reset_password_with_valid_token_succeeds(client, monkeypatch, db_session):
    monkeypatch.setattr(auth_module, "send_password_reset_email", _noop_email)
    email = "valid-reset@example.com"
    client.post("/auth/signup", json={"email": email, "password": "oldpass1"})
    client.post("/auth/forgot-password", json={"email": email})

    token = _get_reset_token_for_email(db_session, email)

    response = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "newpass2"}
    )
    assert response.status_code == 200

    old_login = client.post("/auth/login", data={"username": email, "password": "oldpass1"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", data={"username": email, "password": "newpass2"})
    assert new_login.status_code == 200


def test_reset_password_token_cannot_be_reused(client, monkeypatch, db_session):
    monkeypatch.setattr(auth_module, "send_password_reset_email", _noop_email)
    email = "reuse-test@example.com"
    client.post("/auth/signup", json={"email": email, "password": "oldpass1"})
    client.post("/auth/forgot-password", json={"email": email})
    token = _get_reset_token_for_email(db_session, email)

    first = client.post("/auth/reset-password", json={"token": token, "new_password": "newpass2"})
    assert first.status_code == 200

    second = client.post("/auth/reset-password", json={"token": token, "new_password": "newpass3"})
    assert second.status_code == 400


def test_reset_password_rejects_invalid_token(client):
    response = client.post(
        "/auth/reset-password", json={"token": "not-a-real-token", "new_password": "newpass2"}
    )
    assert response.status_code == 400


def test_reset_password_rejects_weak_new_password(client, monkeypatch, db_session):
    monkeypatch.setattr(auth_module, "send_password_reset_email", _noop_email)
    email = "weak-new-pw@example.com"
    client.post("/auth/signup", json={"email": email, "password": "oldpass1"})
    client.post("/auth/forgot-password", json={"email": email})
    token = _get_reset_token_for_email(db_session, email)

    response = client.post("/auth/reset-password", json={"token": token, "new_password": "short1"})
    assert response.status_code == 422


def test_reset_password_clears_login_lockout(client, monkeypatch, db_session):
    monkeypatch.setattr(auth_module, "send_password_reset_email", _noop_email)
    email = "locked-then-reset@example.com"
    client.post("/auth/signup", json={"email": email, "password": "oldpass1"})

    for _ in range(5):
        client.post("/auth/login", data={"username": email, "password": "wrongpass"})

    still_locked = client.post("/auth/login", data={"username": email, "password": "oldpass1"})
    assert still_locked.status_code == 429

    client.post("/auth/forgot-password", json={"email": email})
    token = _get_reset_token_for_email(db_session, email)
    client.post("/auth/reset-password", json={"token": token, "new_password": "newpass2"})

    unlocked_login = client.post("/auth/login", data={"username": email, "password": "newpass2"})
    assert unlocked_login.status_code == 200
