"""POST /payments/create — оплата из внутреннего кошелька."""

import uuid
from decimal import Decimal
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.listing import ListingStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.reissue import ReissueRequest, ReissueStatus
from app.models.user import User
from app.services.audit import log_event

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.post("/create")
@jwt_required()
def create_payment():
    """
    Оплата заказа из внутреннего кошелька пользователя.
    Идемпотентен: если платёж уже подтверждён, вернёт его повторно.
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

    existing = Payment.query.filter_by(order_id=order.id).first()
    if existing and existing.status == PaymentStatus.CONFIRMED:
        return jsonify({"payment": existing.to_dict()})

    if order.status != OrderStatus.PENDING_PAYMENT:
        return jsonify({"error": "order is not awaiting payment"}), 409

    if existing and existing.status == PaymentStatus.CREATED:
        payment = existing
    else:
        payment = Payment(
            order_id=order.id,
            provider="wallet",
            provider_payment_id=f"wallet-{uuid.uuid4().hex[:12]}",
            amount=order.amount,
            currency="rub",
            status=PaymentStatus.CREATED,
            checkout_url=None,
        )
        db.session.add(payment)
        db.session.flush()

    buyer = User.query.get(user_id)
    if not buyer:
        return jsonify({"error": "user not found"}), 404

    if Decimal(str(buyer.balance or 0)) < Decimal(str(order.amount)):
        payment.status = PaymentStatus.FAILED
        order.status = OrderStatus.CANCELLED
        if order.listing:
            order.listing.status = ListingStatus.ACTIVE
        db.session.commit()

        log_event(
            "PAYMENT_FAILED",
            "payment",
            str(payment.id),
            user_id,
            {"order_id": str(order.id), "reason": "insufficient_wallet_balance"},
        )
        return jsonify({"error": "insufficient wallet balance"}), 400

    _confirm_payment(
        order, payment, buyer, event_id=f"wallet-evt-{uuid.uuid4().hex[:8]}"
    )

    log_event(
        "PAYMENT_CONFIRMED",
        "payment",
        str(payment.id),
        user_id,
        {
            "order_id": str(order.id),
            "amount": float(order.amount),
            "provider": "wallet",
        },
    )

    return jsonify({"payment": payment.to_dict()}), 201


# ─── helpers ────────────────────────────────────────────────────────────────


def _confirm_payment(
    order: Order, payment: Payment, buyer: User, event_id: str
) -> None:
    """Списывает деньги с покупателя, подтверждает платёж и запускает переоформление."""
    payment.provider_event_id = event_id
    payment.status = PaymentStatus.CONFIRMED
    order.status = OrderStatus.PAID
    buyer.balance = Decimal(str(buyer.balance or 0)) - Decimal(str(order.amount))

    db.session.commit()
    log_event(
        "WALLET_DEBITED",
        "user",
        str(buyer.id),
        details={"order_id": str(order.id), "amount": float(order.amount)},
    )
    _trigger_reissue(order)


def _trigger_reissue(order: Order) -> None:
    """Создаёт ReissueRequest и ставит задачу в Celery."""
    from flask import current_app
    from app.tasks.reissue_tasks import process_reissue

    ticket = order.listing.ticket
    reissue = ReissueRequest(
        ticket_id=ticket.id,
        order_id=order.id,
        status=ReissueStatus.PENDING,
    )
    db.session.add(reissue)
    db.session.commit()

    log_event(
        "REISSUE_REQUESTED",
        "reissue",
        str(reissue.id),
        details={"order_id": str(order.id)},
    )

    if current_app.config.get("TESTING"):
        process_reissue.run(str(reissue.id))
        return

    process_reissue.delay(str(reissue.id))
