"""POST /payments/create, POST /payments/webhook (YooKassa / debug auto-confirm)"""
import logging
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.reissue import ReissueRequest, ReissueStatus
from app.services.audit import log_event

logger = logging.getLogger(__name__)

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.post("/create")
@jwt_required()
def create_payment():
    """
    FR3: Создание платежа для заказа.
    DEBUG=true → авто-подтверждение без внешней оплаты.
    PROD → YooKassa, возвращает checkout_url для редиректа.
    Идемпотентен: повторный вызов вернёт существующий CREATED платёж.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"error": "order_id is required"}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    if str(order.buyer_user_id) != user_id:
        return jsonify({"error": "forbidden"}), 403

    if order.status != OrderStatus.PENDING_PAYMENT:
        return jsonify({"error": "order is not awaiting payment"}), 409

    # Идемпотентность: если платёж уже создан — возвращаем существующий
    existing = Payment.query.filter_by(order_id=order.id).first()
    if existing and existing.status == PaymentStatus.CREATED:
        return jsonify({"payment": existing.to_dict()})

    # ─── DEBUG-режим: автоматическое подтверждение (реальных денег нет) ───
    if current_app.config.get("DEBUG"):
        payment = Payment(
            order_id=order.id,
            provider="debug",
            provider_payment_id=f"debug-{uuid.uuid4().hex[:12]}",
            amount=order.amount,
            currency="rub",
            status=PaymentStatus.CREATED,
            checkout_url=None,  # нет редиректа — сразу на страницу заказа
        )
        db.session.add(payment)
        db.session.flush()

        _confirm_payment(order, payment, event_id=f"debug-evt-{uuid.uuid4().hex[:8]}")

        log_event("PAYMENT_CREATED", "payment", str(payment.id), user_id,
                  {"order_id": str(order.id), "amount": float(order.amount), "mode": "debug_auto"})

        return jsonify({"payment": payment.to_dict()}), 201

    # ─── PROD: YooKassa ───
    try:
        from yookassa import Configuration, Payment as YooPayment
        Configuration.account_id = current_app.config["YOOKASSA_SHOP_ID"]
        Configuration.secret_key = current_app.config["YOOKASSA_SECRET_KEY"]

        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
        yk = YooPayment.create({
            "amount": {"value": f"{float(order.amount):.2f}", "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"{frontend_url}/orders/{order.id}?success=1",
            },
            "capture": True,
            "description": f"Билет — заказ #{str(order.id)[:8]}",
            "metadata": {"order_id": str(order.id)},
        }, idempotency_key=f"order-{str(order.id)}")
    except Exception as e:
        logger.error("YooKassa error: %s", e)
        return jsonify({"error": "payment provider error", "detail": str(e)}), 502

    checkout_url = yk.confirmation.confirmation_url if yk.confirmation else None

    payment = Payment(
        order_id=order.id,
        provider="yookassa",
        provider_payment_id=yk.id,
        amount=order.amount,
        currency="rub",
        status=PaymentStatus.CREATED,
        checkout_url=checkout_url,
    )
    db.session.add(payment)
    db.session.commit()

    log_event("PAYMENT_CREATED", "payment", str(payment.id), user_id,
              {"order_id": str(order.id), "amount": float(order.amount)})

    return jsonify({"payment": payment.to_dict()}), 201


@payments_bp.post("/webhook")
def yookassa_webhook():
    """
    YooKassa webhook: payment.succeeded / payment.canceled.
    В DEBUG-режиме не используется — подтверждение происходит автоматически в /create.
    """
    if current_app.config.get("DEBUG"):
        return jsonify({"status": "ok"})

    data = request.get_json(silent=True) or {}
    event_type = data.get("event")
    obj = data.get("object", {})
    payment_yk_id = obj.get("id")
    event_id = data.get("id") or payment_yk_id

    if not payment_yk_id or not event_type:
        return jsonify({"error": "invalid payload"}), 400

    # Дедупликация
    if Payment.query.filter_by(provider_event_id=event_id).first():
        logger.info("Duplicate webhook event %s — skipping", event_id)
        return jsonify({"status": "duplicate"}), 200

    if event_type == "payment.succeeded":
        metadata = obj.get("metadata", {})
        order_id = metadata.get("order_id")
        if not order_id:
            return jsonify({"error": "missing order_id in metadata"}), 400

        order = Order.query.get(order_id)
        payment = Payment.query.filter_by(provider_payment_id=payment_yk_id).first()

        if not order or not payment:
            logger.error("Order/payment not found: order=%s payment_id=%s", order_id, payment_yk_id)
            return jsonify({"error": "not found"}), 404

        _confirm_payment(order, payment, event_id=event_id)
        log_event("PAYMENT_CONFIRMED", "payment", str(payment.id),
                  details={"order_id": str(order.id)})

    elif event_type == "payment.canceled":
        metadata = obj.get("metadata", {})
        order_id = metadata.get("order_id")
        if order_id:
            order = Order.query.get(order_id)
            payment = Payment.query.filter_by(provider_payment_id=payment_yk_id).first()
            if order and order.status == OrderStatus.PENDING_PAYMENT:
                order.status = OrderStatus.FAILED
                if payment:
                    payment.provider_event_id = event_id
                    payment.status = PaymentStatus.FAILED
                from app.models.listing import ListingStatus
                if order.listing:
                    order.listing.status = ListingStatus.ACTIVE
                db.session.commit()
                log_event("PAYMENT_FAILED", "payment",
                          str(payment.id) if payment else None,
                          details={"order_id": order_id})

    return jsonify({"status": "ok"})


# ─── helpers ────────────────────────────────────────────────────────────────

PLATFORM_FEE = 0.05  # 5% комиссия платформы


def _confirm_payment(order: Order, payment: Payment, event_id: str) -> None:
    """Помечает платёж подтверждённым, начисляет продавцу и запускает переоформление."""
    from app.models.user import User

    payment.provider_event_id = event_id
    payment.status = PaymentStatus.CONFIRMED
    order.status = OrderStatus.PAID

    # Начисляем продавцу сумму за вычетом комиссии платформы
    seller_id = order.listing.seller_user_id
    seller = User.query.get(seller_id)
    if seller:
        payout = order.amount * (1 - PLATFORM_FEE)
        seller.balance = (seller.balance or 0) + payout
        log_event("WALLET_CREDITED", "user", str(seller.id),
                  details={"order_id": str(order.id), "amount": float(payout)})

    db.session.commit()
    _trigger_reissue(order)


def _trigger_reissue(order: Order) -> None:
    """Создаёт ReissueRequest и ставит задачу в Celery."""
    from app.tasks.reissue_tasks import process_reissue

    ticket = order.listing.ticket
    reissue = ReissueRequest(
        ticket_id=ticket.id,
        order_id=order.id,
        status=ReissueStatus.PENDING,
    )
    db.session.add(reissue)
    db.session.commit()

    log_event("REISSUE_REQUESTED", "reissue", str(reissue.id),
              details={"order_id": str(order.id)})

    process_reissue.delay(str(reissue.id))
