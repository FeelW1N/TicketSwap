"""GET /wallet/balance, POST /wallet/topup, POST /wallet/withdraw"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.services.audit import log_event

wallet_bp = Blueprint("wallet", __name__, url_prefix="/wallet")

MIN_WITHDRAW = 100  # минимальная сумма вывода в рублях


@wallet_bp.get("/balance")
@jwt_required()
def get_balance():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"balance": float(user.balance or 0)})


@wallet_bp.post("/topup")
@jwt_required()
def topup():
    """Учебное пополнение кошелька без реального платёжного провайдера."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    if amount is None or float(amount) <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    amount = float(amount)
    user.balance = float(user.balance or 0) + amount
    db.session.commit()

    log_event(
        "WALLET_TOPUP",
        "user",
        str(user.id),
        details={"amount": amount, "balance": float(user.balance)},
    )

    return jsonify(
        {
            "status": "ok",
            "topped_up": amount,
            "balance": float(user.balance),
        }
    )


@wallet_bp.post("/withdraw")
@jwt_required()
def withdraw():
    """Запрос на вывод средств. В DEBUG — сразу списывает баланс."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    if not amount or float(amount) <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    amount = float(amount)

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    if float(user.balance or 0) < amount:
        return jsonify({"error": "insufficient balance"}), 400

    if amount < MIN_WITHDRAW:
        return jsonify({"error": f"minimum withdrawal is {MIN_WITHDRAW} RUB"}), 400

    user.balance = float(user.balance) - amount
    db.session.commit()

    log_event(
        "WALLET_WITHDRAWN",
        "user",
        str(user.id),
        details={"amount": amount, "remaining": float(user.balance)},
    )

    return jsonify(
        {
            "status": "ok",
            "withdrawn": amount,
            "balance": float(user.balance),
        }
    )
