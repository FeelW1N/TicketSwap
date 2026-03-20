"""Сервис аудита — фиксирует ключевые события системы."""
import logging
from typing import Optional
from flask import request
from app.extensions import db
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def log_event(
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    try:
        ip = request.remote_addr if request else None
    except RuntimeError:
        ip = None

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=ip,
    )
    db.session.add(entry)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Audit log commit failed: %s", e)
