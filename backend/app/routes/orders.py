"""POST /orders, GET /orders/{id}, GET /orders (мои заказы)"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.listing import Listing, ListingStatus
from app.models.order import Order, OrderStatus
from app.services.audit import log_event

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.post("")
@jwt_required()
def create_order():
    """
    FR3: Покупка — создание заказа.
    Создаёт Order со статусом PENDING_PAYMENT, резервирует листинг (BLOCKED).
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    listing_id = data.get("listing_id")
    if not listing_id:
        return jsonify({"error": "listing_id is required"}), 400

    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "listing not found"}), 404

    if listing.status != ListingStatus.ACTIVE:
        return jsonify({"error": "listing is not available"}), 409

    if str(listing.seller_user_id) == user_id:
        return jsonify({"error": "you cannot buy your own listing"}), 422

    # Резервируем листинг
    listing.status = ListingStatus.BLOCKED

    order = Order(
        listing_id=listing.id,
        buyer_user_id=user_id,
        status=OrderStatus.PENDING_PAYMENT,
        amount=listing.price,
    )
    db.session.add(order)
    db.session.commit()

    log_event("ORDER_CREATED", "order", str(order.id), user_id,
              {"listing_id": str(listing.id), "amount": float(listing.price)})

    return jsonify(order.to_dict()), 201


@orders_bp.get("")
@jwt_required()
def list_my_orders():
    """Мои покупки — список заказов текущего пользователя."""
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    pagination = (
        Order.query.filter_by(buyer_user_id=user_id)
        .order_by(Order.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "items": [o.to_dict() for o in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@orders_bp.get("/<uuid:order_id>")
@jwt_required()
def get_order(order_id):
    """FR7: Статус заказа. Включает reissue_request если есть."""
    user_id = get_jwt_identity()
    order = Order.query.get_or_404(str(order_id))

    if str(order.buyer_user_id) != user_id:
        return jsonify({"error": "forbidden"}), 403

    result = order.to_dict()
    if order.payment:
        result["payment"] = order.payment.to_dict()
    if order.reissue_request:
        result["reissue"] = order.reissue_request.to_dict()

    return jsonify(result)


@orders_bp.post("/<uuid:order_id>/cancel")
@jwt_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.get_or_404(str(order_id))

    if str(order.buyer_user_id) != user_id:
        return jsonify({"error": "forbidden"}), 403

    if order.status != OrderStatus.PENDING_PAYMENT:
        return jsonify({"error": "order cannot be cancelled in current status"}), 409

    order.status = OrderStatus.CANCELLED
    # Разблокируем листинг
    listing = order.listing
    if listing:
        listing.status = ListingStatus.ACTIVE

    db.session.commit()
    log_event("ORDER_CANCELLED", "order", str(order.id), user_id)
    return jsonify(order.to_dict())
