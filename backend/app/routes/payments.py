"""POST /payments/create, POST /payments/webhook"""
import logging
import stripe
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
    FR3: Создание платежа в Stripe для заказа.
    Возвращает checkout_url для редиректа покупателя.
    Идемпотентен: повторный вызов для существующего CREATED платежа вернёт тот же URL.
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
    existing_payment = Payment.query.filter_by(order_id=order.id).first()
    if existing_payment and existing_payment.status == PaymentStatus.CREATED:
        return jsonify({"payment": existing_payment.to_dict()})

    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "rub",
                    "product_data": {"name": f"Ticket order #{str(order.id)[:8]}"},
                    "unit_amount": int(order.amount * 100),  # копейки
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=current_app.config.get("FRONTEND_URL", "http://localhost:3000") + f"/orders/{order.id}?success=1",
            cancel_url=current_app.config.get("FRONTEND_URL", "http://localhost:3000") + f"/orders/{order.id}?cancelled=1",
            metadata={"order_id": str(order.id)},
            idempotency_key=f"order-{str(order.id)}",
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe error: %s", e)
        return jsonify({"error": "payment provider error", "detail": str(e)}), 502

    payment = Payment(
        order_id=order.id,
        provider="stripe",
        provider_payment_id=checkout_session.id,
        amount=order.amount,
        currency="rub",
        status=PaymentStatus.CREATED,
        checkout_url=checkout_session.url,
    )
    db.session.add(payment)
    db.session.commit()

    log_event("PAYMENT_CREATED", "payment", str(payment.id), user_id,
              {"order_id": str(order.id), "amount": float(order.amount)})

    return jsonify({"payment": payment.to_dict()}), 201


@payments_bp.post("/webhook")
def stripe_webhook():
    """
    FR3: Stripe webhook — подтверждение платежа.
    Идемпотентен по provider_event_id.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = current_app.config["STRIPE_WEBHOOK_SECRET"]

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        return jsonify({"error": "invalid signature"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    event_id = event["id"]
    event_type = event["type"]

    # Дедупликация: не обрабатывать повторные webhook
    if Payment.query.filter_by(provider_event_id=event_id).first():
        logger.info("Duplicate webhook event %s — skipping", event_id)
        return jsonify({"status": "duplicate"}), 200

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        if not order_id:
            return jsonify({"error": "missing order_id in metadata"}), 400

        order = Order.query.get(order_id)
        payment = Payment.query.filter_by(provider_payment_id=session["id"]).first()

        if not order or not payment:
            logger.error("Order or payment not found for webhook: order=%s", order_id)
            return jsonify({"error": "not found"}), 404

        payment.provider_event_id = event_id
        payment.status = PaymentStatus.CONFIRMED
        order.status = OrderStatus.PAID
        db.session.commit()

        log_event("PAYMENT_CONFIRMED", "payment", str(payment.id),
                  details={"order_id": str(order.id)})

        # FR4: Запускаем переоформление асинхронно
        _trigger_reissue(order)

    elif event_type in ("checkout.session.expired", "payment_intent.payment_failed"):
        session = event["data"]["object"]
        order_id = (session.get("metadata") or {}).get("order_id")
        if order_id:
            order = Order.query.get(order_id)
            payment = Payment.query.filter_by(provider_payment_id=session.get("id")).first()
            if order and order.status == OrderStatus.PENDING_PAYMENT:
                order.status = OrderStatus.FAILED
                if payment:
                    payment.provider_event_id = event_id
                    payment.status = PaymentStatus.FAILED
                # Разблокируем листинг
                from app.models.listing import ListingStatus
                if order.listing:
                    order.listing.status = ListingStatus.ACTIVE
                db.session.commit()
                log_event("PAYMENT_FAILED", "payment",
                          str(payment.id) if payment else None,
                          details={"order_id": order_id})

    return jsonify({"status": "ok"})


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
