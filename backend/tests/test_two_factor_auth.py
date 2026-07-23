import pyotp


def _signup_and_login(client, email="2fa-test@example.com", password="testpass1"):
    client.post("/auth/signup", json={"email": email, "password": password})
    login = client.post("/auth/login", data={"username": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email, password


def test_2fa_setup_returns_secret_and_uri_but_does_not_enable_yet(client):
    headers, _, _ = _signup_and_login(client)
    response = client.post("/auth/2fa/setup", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "secret" in body
    assert body["provisioning_uri"].startswith("otpauth://")

    me = client.get("/auth/me", headers=headers)
    assert me.json()["totp_enabled"] is False


def test_2fa_verify_enables_it_with_correct_code(client):
    headers, _, _ = _signup_and_login(client)
    setup = client.post("/auth/2fa/setup", headers=headers).json()
    code = pyotp.TOTP(setup["secret"]).now()

    response = client.post("/auth/2fa/verify", json={"code": code}, headers=headers)
    assert response.status_code == 200
    assert response.json()["totp_enabled"] is True


def test_2fa_verify_rejects_wrong_code(client):
    headers, _, _ = _signup_and_login(client)
    client.post("/auth/2fa/setup", headers=headers)

    response = client.post("/auth/2fa/verify", json={"code": "000000"}, headers=headers)
    assert response.status_code == 401


def test_login_requires_2fa_code_once_enabled(client):
    headers, email, password = _signup_and_login(client)
    setup = client.post("/auth/2fa/setup", headers=headers).json()
    code = pyotp.TOTP(setup["secret"]).now()
    client.post("/auth/2fa/verify", json={"code": code}, headers=headers)

    without_code = client.post("/auth/login", data={"username": email, "password": password})
    assert without_code.status_code == 400
    assert "2fa" in without_code.json()["detail"].lower()

    fresh_code = pyotp.TOTP(setup["secret"]).now()
    with_code = client.post(
        "/auth/login",
        data={"username": email, "password": password, "totp_code": fresh_code},
    )
    assert with_code.status_code == 200


def test_login_rejects_wrong_2fa_code(client):
    headers, email, password = _signup_and_login(client)
    setup = client.post("/auth/2fa/setup", headers=headers).json()
    code = pyotp.TOTP(setup["secret"]).now()
    client.post("/auth/2fa/verify", json={"code": code}, headers=headers)

    response = client.post(
        "/auth/login",
        data={"username": email, "password": password, "totp_code": "000000"},
    )
    assert response.status_code == 401


def test_2fa_disable_requires_valid_code(client):
    headers, _, _ = _signup_and_login(client)
    setup = client.post("/auth/2fa/setup", headers=headers).json()
    code = pyotp.TOTP(setup["secret"]).now()
    client.post("/auth/2fa/verify", json={"code": code}, headers=headers)

    wrong_attempt = client.post("/auth/2fa/disable", json={"code": "000000"}, headers=headers)
    assert wrong_attempt.status_code == 401

    fresh_code = pyotp.TOTP(setup["secret"]).now()
    correct_attempt = client.post(
        "/auth/2fa/disable", json={"code": fresh_code}, headers=headers
    )
    assert correct_attempt.status_code == 200
    assert correct_attempt.json()["totp_enabled"] is False
