"""POST /listings, GET /listings, GET /listings/{id}, DELETE /listings/{id}"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.event import Event
from app.models.ticket import Ticket, TicketStatus
from app.models.listing import Listing, ListingStatus
from app.services.storage import storage_service
from app.services.organizer import get_organizer_adapter
from app.services.audit import log_event
from app.config import Config

logger = logging.getLogger(__name__)

listings_bp = Blueprint("listings", __name__, url_prefix="/listings")

ALLOWED_EXTENSIONS = Config.ALLOWED_FILE_EXTENSIONS
MAX_FILE_BYTES = Config.MAX_FILE_SIZE_MB * 1024 * 1024


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@listings_bp.post("")
@jwt_required()
def create_listing():
    """
    FR1: Публикация объявления.
    Мультипарт-форма: поля JSON + опциональный файл билета.
    """
    user_id = get_jwt_identity()

    # Поддерживаем как multipart, так и JSON
    if request.content_type and "multipart" in request.content_type:
        data = request.form.to_dict()
        file = request.files.get("ticket_file")
    else:
        data = request.get_json(silent=True) or {}
        file = None

    # Валидация обязательных полей
    for field in ["event_id", "price", "external_ticket_id", "organizer_id"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    try:
        price = float(data["price"])
    except (ValueError, TypeError):
        return jsonify({"error": "price must be a number"}), 400

    event = Event.query.get(data["event_id"])
    if not event:
        return jsonify({"error": "event not found"}), 404

    # Проверка: нет ли уже такого билета в системе
    existing_ticket = Ticket.query.filter_by(
        organizer_id=data["organizer_id"],
        external_ticket_id=data["external_ticket_id"],
    ).first()
    if existing_ticket and existing_ticket.status != TicketStatus.CANCELLED:
        return jsonify({"error": "ticket already listed or sold"}), 409

    # FR2: Верификация у организатора
    adapter = get_organizer_adapter()
    validation = adapter.validate_ticket(
        organizer_id=data["organizer_id"],
        external_ticket_id=data["external_ticket_id"],
        seller_user_id=user_id,
    )
    if not validation.is_valid:
        return jsonify({"error": "ticket validation failed", "detail": validation.error}), 422

    # Проверка наценки: не более 20% от исходной цены
    if validation.face_value:
        max_price = validation.face_value * (1 + Config.MAX_RESALE_MARKUP_PERCENT / 100)
        if price > max_price:
            return jsonify({
                "error": f"price exceeds allowed markup (max {max_price:.2f})"
            }), 422

    # Загрузка файла в S3
    s3_key = None
    if file and _allowed_file(file.filename):
        file_bytes = file.read()
        if len(file_bytes) > MAX_FILE_BYTES:
            return jsonify({"error": f"file too large (max {Config.MAX_FILE_SIZE_MB}MB)"}), 413
        s3_key = storage_service.upload_ticket_file(file_bytes, file.filename, user_id)

    # Создание сущностей
    ticket = Ticket(
        external_ticket_id=data["external_ticket_id"],
        organizer_id=data["organizer_id"],
        owner_user_id=user_id,
        event_id=data["event_id"],
        status=TicketStatus.ACTIVE,
        seat_info=data.get("seat_info"),
        face_value=validation.face_value or data.get("face_value"),
        s3_key=s3_key,
    )
    db.session.add(ticket)
    db.session.flush()

    listing = Listing(
        ticket_id=ticket.id,
        event_id=data["event_id"],
        seller_user_id=user_id,
        price=price,
        description=data.get("description"),
        status=ListingStatus.ACTIVE,
    )
    db.session.add(listing)
    db.session.commit()

    log_event("LISTING_CREATED", "listing", str(listing.id), user_id,
              {"price": price, "event_id": data["event_id"]})

    return jsonify(listing.to_dict(include_event=True, include_ticket=True)), 201


@listings_bp.get("")
def list_listings():
    """Список активных объявлений."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    event_id = request.args.get("event_id")

    query = Listing.query.filter_by(status=ListingStatus.ACTIVE)
    if event_id:
        query = query.filter_by(event_id=event_id)

    pagination = query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "items": [l.to_dict(include_event=True, include_ticket=True) for l in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@listings_bp.get("/<uuid:listing_id>")
def get_listing(listing_id):
    listing = Listing.query.get_or_404(str(listing_id))
    return jsonify(listing.to_dict(include_event=True, include_ticket=True))


@listings_bp.delete("/<uuid:listing_id>")
@jwt_required()
def cancel_listing(listing_id):
    user_id = get_jwt_identity()
    listing = Listing.query.get_or_404(str(listing_id))

    if str(listing.seller_user_id) != user_id:
        return jsonify({"error": "forbidden"}), 403

    if listing.status != ListingStatus.ACTIVE:
        return jsonify({"error": "listing is not active"}), 409

    listing.status = ListingStatus.BLOCKED
    listing.ticket.status = TicketStatus.CANCELLED
    db.session.commit()

    log_event("LISTING_CANCELLED", "listing", str(listing.id), user_id)
    return jsonify({"message": "listing cancelled"})
