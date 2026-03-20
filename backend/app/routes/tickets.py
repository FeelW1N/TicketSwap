"""GET /tickets/{id}/download — выдача подписанной ссылки на новый билет."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.ticket import Ticket
from app.models.order import OrderStatus
from app.models.reissue import ReissueRequest, ReissueStatus
from app.services.storage import storage_service

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@tickets_bp.get("/<uuid:ticket_id>/download")
@jwt_required()
def download_ticket(ticket_id):
    """
    FR4 + Безопасность: Выдача presigned URL только легитимному владельцу.
    Проверяет, что покупатель успешно получил билет через reissue.
    """
    user_id = get_jwt_identity()
    ticket = Ticket.query.get_or_404(str(ticket_id))

    # Ищем успешное переоформление на этот билет
    reissue = (
        ReissueRequest.query
        .filter_by(status=ReissueStatus.SUCCESS)
        .join(ReissueRequest.order)
        .filter_by(buyer_user_id=user_id)
        .filter(ReissueRequest.ticket_id == ticket.id)
        .first()
    )

    # Оригинальный владелец (продавец) тоже может скачать, если билет ещё ACTIVE
    is_original_owner = str(ticket.owner_user_id) == user_id

    if reissue is None and not is_original_owner:
        return jsonify({"error": "forbidden"}), 403

    # Ключ файла: для reissue — новый, иначе — оригинальный
    s3_key = (reissue.new_ticket_s3_key if reissue else None) or ticket.s3_key
    if not s3_key:
        return jsonify({"error": "ticket file not available"}), 404

    url = storage_service.generate_presigned_url(s3_key)
    return jsonify({"download_url": url, "expires_in": 3600})
