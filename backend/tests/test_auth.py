"""Unit-тесты: аутентификация."""


def test_register_success(client):
    resp = client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "strongpass1",
        "full_name": "Alice",
    })
    assert resp.status_code == 201
    data = resp.json
    assert "access_token" in data
    assert data["user"]["email"] == "user@example.com"


def test_register_duplicate(client):
    payload = {"email": "dup@example.com", "password": "password1", "full_name": "Dup"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409


def test_register_short_password(client):
    resp = client.post("/auth/register", json={
        "email": "short@example.com", "password": "123", "full_name": "Short"
    })
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@example.com", "password": "mypassword", "full_name": "Login"
    })
    resp = client.post("/auth/login", json={
        "email": "login@example.com", "password": "mypassword"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "email": "wp@example.com", "password": "rightpass", "full_name": "WP"
    })
    resp = client.post("/auth/login", json={
        "email": "wp@example.com", "password": "wrongpass"
    })
    assert resp.status_code == 401


def test_me_authenticated(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert "email" in resp.json


def test_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
