"""Тесты: восстановление пароля и улучшенные ошибки валидации."""
import pytest
from app.models.password_reset import PasswordResetToken


# --------------------------------------------------------------------------- #
# /auth/register — детальные ошибки                                           #
# --------------------------------------------------------------------------- #

def test_register_missing_email(client):
    resp = client.post("/auth/register", json={"password": "pass1234", "full_name": "X"})
    assert resp.status_code == 400
    assert resp.json["code"] == "email_required"


def test_register_invalid_email_format(client):
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "pass1234", "full_name": "X"})
    assert resp.status_code == 400
    assert resp.json["code"] == "invalid_email_format"
    assert "email" in resp.json["error"].lower()


def test_register_missing_name(client):
    resp = client.post("/auth/register", json={"email": "ok@test.com", "password": "pass1234"})
    assert resp.status_code == 400
    assert resp.json["code"] == "full_name_required"


def test_register_password_too_short(client):
    resp = client.post("/auth/register", json={"email": "ok2@test.com", "password": "123", "full_name": "X"})
    assert resp.status_code == 400
    assert resp.json["code"] == "password_too_short"


def test_register_duplicate_email_code(client):
    payload = {"email": "dup2@test.com", "password": "password1", "full_name": "Dup"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json["code"] == "email_already_exists"


# --------------------------------------------------------------------------- #
# /auth/login — детальные ошибки                                              #
# --------------------------------------------------------------------------- #

def test_login_invalid_email_format(client):
    resp = client.post("/auth/login", json={"email": "bad-email", "password": "pass"})
    assert resp.status_code == 400
    assert resp.json["code"] == "invalid_email_format"


def test_login_wrong_credentials_code(client):
    client.post("/auth/register", json={"email": "creds@test.com", "password": "rightpass", "full_name": "U"})
    resp = client.post("/auth/login", json={"email": "creds@test.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json["code"] == "invalid_credentials"


# --------------------------------------------------------------------------- #
# /auth/forgot-password                                                        #
# --------------------------------------------------------------------------- #

def test_forgot_password_existing_user(client, app):
    client.post("/auth/register", json={"email": "reset@test.com", "password": "password1", "full_name": "Reset"})
    resp = client.post("/auth/forgot-password", json={"email": "reset@test.com"})
    assert resp.status_code == 200
    assert "отправлено" in resp.json["message"]
    # DEBUG-режим возвращает токен
    assert "debug_token" in resp.json
    assert len(resp.json["debug_token"]) > 10


def test_forgot_password_unknown_email_same_response(client):
    """Не раскрываем существование email."""
    resp = client.post("/auth/forgot-password", json={"email": "nobody@test.com"})
    assert resp.status_code == 200
    assert "отправлено" in resp.json["message"]
    assert "debug_token" not in resp.json


def test_forgot_password_invalid_email(client):
    resp = client.post("/auth/forgot-password", json={"email": "notanemail"})
    assert resp.status_code == 400
    assert resp.json["code"] == "invalid_email_format"


def test_forgot_password_missing_email(client):
    resp = client.post("/auth/forgot-password", json={})
    assert resp.status_code == 400
    assert resp.json["code"] == "email_required"


# --------------------------------------------------------------------------- #
# /auth/reset-password                                                         #
# --------------------------------------------------------------------------- #

@pytest.fixture
def reset_token(client):
    """Регистрирует пользователя, запрашивает сброс, возвращает токен."""
    client.post("/auth/register", json={"email": "tok@test.com", "password": "oldpassword", "full_name": "Tok"})
    resp = client.post("/auth/forgot-password", json={"email": "tok@test.com"})
    return resp.json["debug_token"]


def test_reset_password_success(client, reset_token):
    resp = client.post("/auth/reset-password", json={"token": reset_token, "password": "newpassword"})
    assert resp.status_code == 200
    assert "изменён" in resp.json["message"]


def test_reset_password_can_login_with_new(client, reset_token):
    client.post("/auth/reset-password", json={"token": reset_token, "password": "newpass99"})
    resp = client.post("/auth/login", json={"email": "tok@test.com", "password": "newpass99"})
    assert resp.status_code == 200
    assert "access_token" in resp.json


def test_reset_password_old_password_fails(client, reset_token):
    client.post("/auth/reset-password", json={"token": reset_token, "password": "newpass99"})
    resp = client.post("/auth/login", json={"email": "tok@test.com", "password": "oldpassword"})
    assert resp.status_code == 401


def test_reset_token_used_only_once(client, reset_token):
    client.post("/auth/reset-password", json={"token": reset_token, "password": "newpass99"})
    resp = client.post("/auth/reset-password", json={"token": reset_token, "password": "another"})
    assert resp.status_code == 400
    assert resp.json["code"] == "token_invalid"


def test_reset_password_wrong_token(client):
    resp = client.post("/auth/reset-password", json={"token": "fakefakefake", "password": "newpass99"})
    assert resp.status_code == 400
    assert resp.json["code"] == "token_invalid"


def test_reset_password_missing_token(client):
    resp = client.post("/auth/reset-password", json={"password": "newpass99"})
    assert resp.status_code == 400
    assert resp.json["code"] == "token_required"


def test_reset_password_too_short(client, reset_token):
    resp = client.post("/auth/reset-password", json={"token": reset_token, "password": "short"})
    assert resp.status_code == 400
    assert resp.json["code"] == "password_too_short"


def test_reset_expired_token(client, app):
    """Просроченный токен возвращает token_expired."""
    from datetime import datetime, timezone, timedelta
    client.post("/auth/register", json={"email": "exp@test.com", "password": "password1", "full_name": "Exp"})
    resp = client.post("/auth/forgot-password", json={"email": "exp@test.com"})
    token_value = resp.json["debug_token"]

    # Вручную просрочиваем токен
    with app.app_context():
        from app.extensions import db
        tok = PasswordResetToken.query.filter_by(token=token_value).first()
        tok.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.session.commit()

    resp2 = client.post("/auth/reset-password", json={"token": token_value, "password": "newpass99"})
    assert resp2.status_code == 400
    assert resp2.json["code"] == "token_expired"
