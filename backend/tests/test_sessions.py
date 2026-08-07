from datetime import timedelta

from app.core.time import utcnow
from app.models.user import User
from app.models.user_session import UserSession

UA_CHROME_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
UA_SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
UA_FIREFOX_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
)


def _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS):
    client.post("/auth/signup", json={"email": email, "password": "password123"})
    user = db_session.query(User).filter(User.email == email).first()
    if user:
        user.email_verified = True
        db_session.commit()
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "password123"},
        headers={"User-Agent": user_agent},
    )
    return response


def test_login_creates_a_session(client, db_session):
    email = "device1@example.com"
    response = _signup_and_login(client, db_session, email)
    assert response.status_code == 200

    sessions = db_session.query(UserSession).all()
    assert len(sessions) == 1
    assert "Chrome" in sessions[0].device_label


def test_third_device_login_is_blocked(client, db_session):
    email = "device2@example.com"
    first = _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS)
    second = _signup_and_login(client, db_session, email, user_agent=UA_SAFARI_IPHONE)
    third = _signup_and_login(client, db_session, email, user_agent=UA_FIREFOX_MAC)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 403
    assert "maximum of 2 devices" in third.json()["detail"].lower()


def test_logout_frees_a_device_slot(client, db_session):
    email = "device3@example.com"
    first = _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS)
    second = _signup_and_login(client, db_session, email, user_agent=UA_SAFARI_IPHONE)

    logout_response = client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {first.json()['access_token']}"}
    )
    assert logout_response.status_code == 200

    third = _signup_and_login(client, db_session, email, user_agent=UA_FIREFOX_MAC)
    assert third.status_code == 200


def test_logged_out_token_no_longer_authenticates(client, db_session):
    email = "device4@example.com"
    login_response = _signup_and_login(client, db_session, email)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/auth/me", headers=headers).status_code == 200
    client.post("/auth/logout", headers=headers)
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_list_sessions_shows_devices_with_current_flagged(client, db_session):
    email = "device5@example.com"
    first = _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS)
    second = _signup_and_login(client, db_session, email, user_agent=UA_SAFARI_IPHONE)

    headers = {"Authorization": f"Bearer {second.json()['access_token']}"}
    response = client.get("/auth/sessions", headers=headers)
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 2

    current = next(s for s in sessions if s["is_current"])
    other = next(s for s in sessions if not s["is_current"])
    assert "Safari" in current["device_label"]
    assert "Chrome" in other["device_label"]


def test_delete_specific_session_logs_out_that_device(client, db_session):
    email = "device6@example.com"
    first = _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS)
    second = _signup_and_login(client, db_session, email, user_agent=UA_SAFARI_IPHONE)

    second_headers = {"Authorization": f"Bearer {second.json()['access_token']}"}
    first_headers = {"Authorization": f"Bearer {first.json()['access_token']}"}

    sessions = client.get("/auth/sessions", headers=second_headers).json()
    chrome_session_id = next(s["id"] for s in sessions if "Chrome" in s["device_label"])

    delete_response = client.delete(f"/auth/sessions/{chrome_session_id}", headers=second_headers)
    assert delete_response.status_code == 204

    # The deleted device's own token is now invalid, since its session row is gone.
    assert client.get("/auth/me", headers=first_headers).status_code == 401
    # The device that did the deleting is unaffected.
    assert client.get("/auth/me", headers=second_headers).status_code == 200


def test_cannot_delete_another_users_session(client, db_session, make_user):
    email = "device7@example.com"
    owner_login = _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS)
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}
    owner_session_id = client.get("/auth/sessions", headers=owner_headers).json()[0]["id"]

    _, other_token = make_user()
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.delete(f"/auth/sessions/{owner_session_id}", headers=other_headers)
    assert response.status_code == 404


def test_expired_session_does_not_count_toward_device_limit(client, db_session):
    email = "device8@example.com"
    first = _signup_and_login(client, db_session, email, user_agent=UA_CHROME_WINDOWS)
    second = _signup_and_login(client, db_session, email, user_agent=UA_SAFARI_IPHONE)

    # Simulate the first session having expired, without waiting 24 hours.
    session_a = db_session.query(UserSession).filter(UserSession.device_label.contains("Chrome")).first()
    session_a.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()

    third = _signup_and_login(client, db_session, email, user_agent=UA_FIREFOX_MAC)
    assert third.status_code == 200


def test_signup_rejects_disposable_email_domain(client):
    response = client.post(
        "/auth/signup", json={"email": "student@mailinator.com", "password": "password123"}
    )
    assert response.status_code == 422
    assert "permanent email" in response.text.lower()


def test_signup_allows_normal_email_domain(client):
    response = client.post(
        "/auth/signup", json={"email": "student@gmail.com", "password": "password123"}
    )
    assert response.status_code == 201
