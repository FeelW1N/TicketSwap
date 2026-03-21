"""POST /listings, GET /listings, GET /listings/{id}, DELETE /listings/{id}"""
import logging
from flask import Blueprint, request, jsonify, current_app
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

    # Валидация обязательных полей (price проверяем отдельно, т.к. 0 — falsy)
    for field in ["event_id", "external_ticket_id", "organizer_id"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if data.get("price") is None:
        return jsonify({"error": "price is required"}), 400

    try:
        price = float(data["price"])
    except (ValueError, TypeError):
        return jsonify({"error": "price must be a number"}), 400

    if price <= 0:
        return jsonify({"error": "price must be positive"}), 400

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

    # Проверка наценки: не более 20% от исходной цены (в DEBUG пропускаем)
    if validation.face_value and not current_app.config.get("DEBUG"):
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
    """Список активных объявлений с поиском, фильтрами и сортировкой.

    Query params:
      q        — поиск по названию события или городу
      city     — фильтр по городу
      category — фильтр по категории (concert, sport, theatre...)
      sort     — price_asc | price_desc | date_asc | date_desc | newest (default)
      page, per_page
    """
    from app.models.event import Event as EventModel
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 12, type=int), 100)
    event_id = request.args.get("event_id")
    q = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "newest")

    query = Listing.query.join(EventModel, Listing.event_id == EventModel.id)\
        .filter(Listing.status == ListingStatus.ACTIVE)

    if event_id:
        query = query.filter(Listing.event_id == event_id)
    if q:
        query = query.filter(
            db.or_(
                EventModel.title.ilike(f"%{q}%"),
                EventModel.city.ilike(f"%{q}%"),
                EventModel.venue.ilike(f"%{q}%"),
            )
        )
    if city:
        query = query.filter(EventModel.city.ilike(f"%{city}%"))
    if category:
        query = query.filter(EventModel.category == category)

    sort_map = {
        "price_asc":  Listing.price.asc(),
        "price_desc": Listing.price.desc(),
        "date_asc":   EventModel.event_date.asc(),
        "date_desc":  EventModel.event_date.desc(),
        "newest":     Listing.created_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Listing.created_at.desc()))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
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
