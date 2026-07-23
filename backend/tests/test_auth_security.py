def test_signup_rejects_short_password(client):
    response = client.post(
        "/auth/signup", json={"email": "shortpw@example.com", "password": "abc123"}
    )
    assert response.status_code == 422


def test_signup_rejects_password_without_number(client):
    response = client.post(
        "/auth/signup", json={"email": "noletters@example.com", "password": "abcdefgh"}
    )
    assert response.status_code == 422


def test_signup_rejects_password_without_letter(client):
    response = client.post(
        "/auth/signup", json={"email": "nonumber@example.com", "password": "12345678"}
    )
    assert response.status_code == 422


def test_signup_accepts_valid_password(client):
    response = client.post(
        "/auth/signup", json={"email": "validpw@example.com", "password": "goodpass1"}
    )
    assert response.status_code == 201


def test_login_locks_account_after_max_failed_attempts(client):
    email = "lockout-test@example.com"
    client.post("/auth/signup", json={"email": email, "password": "correctpass1"})

    for _ in range(5):
        response = client.post(
            "/auth/login", data={"username": email, "password": "wrongpassword"}
        )
        assert response.status_code == 401

    locked_response = client.post(
        "/auth/login", data={"username": email, "password": "correctpass1"}
    )
    assert locked_response.status_code == 429
    assert "try again" in locked_response.json()["detail"].lower()


def test_successful_login_resets_failed_attempt_counter(client):
    email = "reset-test@example.com"
    client.post("/auth/signup", json={"email": email, "password": "correctpass1"})

    client.post("/auth/login", data={"username": email, "password": "wrong1"})
    client.post("/auth/login", data={"username": email, "password": "wrong2"})

    success = client.post("/auth/login", data={"username": email, "password": "correctpass1"})
    assert success.status_code == 200

    for _ in range(4):
        response = client.post(
            "/auth/login", data={"username": email, "password": "wrongagain"}
        )
        assert response.status_code == 401

    still_ok = client.post("/auth/login", data={"username": email, "password": "correctpass1"})
    assert still_ok.status_code == 200


def test_login_with_nonexistent_email_does_not_error(client):
    response = client.post(
        "/auth/login", data={"username": "doesnotexist@example.com", "password": "whatever1"}
    )
    assert response.status_code == 401
