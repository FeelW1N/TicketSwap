import uuid
from datetime import datetime, timezone
from app.extensions import db


class ReissueStatus:
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ReissueRequest(db.Model):
    __tablename__ = "reissue_requests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id"), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default=ReissueStatus.PENDING)
    external_new_ticket_id = db.Column(db.String(255))  # ID нового билета у организатора
    new_ticket_s3_key = db.Column(db.String(500))       # ключ нового файла в S3
    error_code = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "ticket_id": str(self.ticket_id),
            "order_id": str(self.order_id),
            "status": self.status,
            "external_new_ticket_id": self.external_new_ticket_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
