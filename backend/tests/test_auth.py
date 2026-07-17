def test_signup_creates_user(client):
    response = client.post("/auth/signup", json={"email": "new@example.com", "password": "password123"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "student"
    assert body["subscription_status"] == "free"
    assert "password" not in body
    assert "password_hash" not in body


def test_signup_rejects_duplicate_email(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    response = client.post("/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    assert response.status_code == 400


def test_login_with_correct_credentials_returns_token(client):
    client.post("/auth/signup", json={"email": "login@example.com", "password": "password123"})
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails(client):
    client.post("/auth/signup", json={"email": "login2@example.com", "password": "password123"})
    response = client.post(
        "/auth/login",
        data={"username": "login2@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "student"
