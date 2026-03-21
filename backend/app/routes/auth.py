"""POST /auth/register, POST /auth/login, GET /auth/me,
   POST /auth/forgot-password, POST /auth/reset-password"""
import re
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
from app.extensions import db
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.services.audit import log_event
from app.services.email import send_password_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Русские сообщения об ошибках для конкретных кодов
_ERRORS = {
    "email_required":        "Укажите email",
    "password_required":     "Укажите пароль",
    "full_name_required":    "Укажите ваше имя",
    "invalid_email_format":  "Некорректный формат email",
    "password_too_short":    "Пароль должен содержать минимум 8 символов",
    "email_already_exists":  "Этот email уже зарегистрирован",
    "invalid_credentials":   "Неверный email или пароль",
    "account_disabled":      "Аккаунт заблокирован. Обратитесь в поддержку",
    "token_required":        "Укажите токен сброса пароля",
    "token_invalid":         "Ссылка недействительна или уже использована",
    "token_expired":         "Ссылка истекла. Запросите новую",
}


def _err(code: str, status: int = 400):
    return jsonify({"error": _ERRORS.get(code, code), "code": code}), status


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    full_name = (data.get("full_name") or "").strip()

    if not email:
        return _err("email_required")
    if not EMAIL_RE.match(email):
        return _err("invalid_email_format")
    if not full_name:
        return _err("full_name_required")
    if not password:
        return _err("password_required")
    if len(password) < 8:
        return _err("password_too_short")
    if User.query.filter_by(email=email).first():
        return _err("email_already_exists", 409)

    user = User(email=email, full_name=full_name, phone=data.get("phone"))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    log_event("USER_REGISTERED", "user", str(user.id), str(user.id))

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email:
        return _err("email_required")
    if not EMAIL_RE.match(email):
        return _err("invalid_email_format")
    if not password:
        return _err("password_required")

    user = User.query.filter_by(email=email).first()
    if user and not user.is_active:
        return _err("account_disabled", 403)
    if not user or not user.check_password(password):
        return _err("invalid_credentials", 401)

    log_event("USER_LOGIN", "user", str(user.id), str(user.id))

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first_or_404()
    return jsonify(user.to_dict())


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token})


@auth_bp.post("/forgot-password")
def forgot_password():
    """Запрашивает сброс пароля — генерирует токен и отправляет email."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return _err("email_required")
    if not EMAIL_RE.match(email):
        return _err("invalid_email_format")

    user = User.query.filter_by(email=email, is_active=True).first()

    # Всегда отвечаем одинаково — не раскрываем существование email
    generic_ok = jsonify({"message": "Если этот email зарегистрирован — письмо отправлено"})

    if not user:
        return generic_ok, 200

    # Инвалидируем предыдущие неиспользованные токены
    PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({"used": True})

    reset_token = PasswordResetToken.create_for_user(str(user.id))
    db.session.add(reset_token)
    db.session.commit()

    try:
        send_password_reset_email(user.email, user.full_name, reset_token.token)
    except Exception:
        pass  # Не прерываем запрос при ошибке отправки

    log_event("PASSWORD_RESET_REQUESTED", "user", str(user.id), str(user.id))

    response = {"message": "Если этот email зарегистрирован — письмо отправлено"}
    # В DEBUG возвращаем токен прямо в ответе для тестирования без email
    if current_app.config.get("DEBUG"):
        response["debug_token"] = reset_token.token
    return jsonify(response), 200


@auth_bp.post("/reset-password")
def reset_password():
    """Устанавливает новый пароль по токену из письма."""
    data = request.get_json(silent=True) or {}
    token_value = (data.get("token") or "").strip()
    new_password = data.get("password", "")

    if not token_value:
        return _err("token_required")

    reset_token = PasswordResetToken.query.filter_by(token=token_value).first()

    if not reset_token:
        return _err("token_invalid", 400)

    from datetime import datetime
    if reset_token.used:
        return _err("token_invalid", 400)
    if datetime.utcnow() >= reset_token.expires_at:
        return _err("token_expired", 400)

    if not new_password:
        return _err("password_required")
    if len(new_password) < 8:
        return _err("password_too_short")

    user = reset_token.user
    user.set_password(new_password)
    reset_token.used = True
    db.session.commit()

    log_event("PASSWORD_RESET_DONE", "user", str(user.id), str(user.id))
    return jsonify({"message": "Пароль успешно изменён"})
