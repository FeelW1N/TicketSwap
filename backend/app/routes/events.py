"""GET /events, GET /events/{id}, POST /events"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.event import Event

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.get("")
def list_events():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    q = request.args.get("q", "")
    city = request.args.get("city", "")

    query = Event.query
    if q:
        query = query.filter(Event.title.ilike(f"%{q}%"))
    if city:
        query = query.filter(Event.city.ilike(f"%{city}%"))

    pagination = query.order_by(Event.event_date).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@events_bp.get("/<uuid:event_id>")
def get_event(event_id):
    event = Event.query.get_or_404(str(event_id))
    return jsonify(event.to_dict())


@events_bp.post("")
@jwt_required()
def create_event():
    data = request.get_json(silent=True) or {}
    required = ["title", "event_date", "organizer_id"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    event = Event(
        title=data["title"],
        description=data.get("description"),
        venue=data.get("venue"),
        city=data.get("city"),
        event_date=data["event_date"],
        organizer_id=data["organizer_id"],
        external_event_id=data.get("external_event_id"),
        category=data.get("category"),
        image_url=data.get("image_url"),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201
