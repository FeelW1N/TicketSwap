import uuid
from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    """Журнал аудита — фиксирует ключевые события системы."""

    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. LISTING_CREATED, ORDER_PAID
    entity_type = db.Column(db.String(50))              # listing, order, payment, reissue
    entity_id = db.Column(db.String(255))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
