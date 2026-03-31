"""GET /organizers, GET /organizers/{id}/events"""

from flask import Blueprint, jsonify
from app.services.organizer import get_organizer_adapter


organizers_bp = Blueprint("organizers", __name__, url_prefix="/organizers")


@organizers_bp.get("")
def list_organizers():
    adapter = get_organizer_adapter()
    try:
        items = [organizer.__dict__ for organizer in adapter.list_organizers()]
        return jsonify({"items": items})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502


@organizers_bp.get("/<organizer_id>/events")
def list_organizer_events(organizer_id):
    adapter = get_organizer_adapter()
    try:
        items = [event.__dict__ for event in adapter.list_events(organizer_id)]
        return jsonify({"items": items})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502
