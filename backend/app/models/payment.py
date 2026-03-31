import uuid
from datetime import datetime, timezone
from app.extensions import db


class PaymentStatus:
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(
        db.String(36), db.ForeignKey("orders.id"), nullable=False, unique=True
    )
    provider = db.Column(db.String(50), nullable=False, default="wallet")
    provider_payment_id = db.Column(
        db.String(255), unique=True
    )  # ID операции во внутреннем кошельке
    provider_event_id = db.Column(
        db.String(255), unique=True
    )  # ID события для идемпотентности
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="rub")
    status = db.Column(db.String(20), nullable=False, default=PaymentStatus.CREATED)
    checkout_url = db.Column(db.String(1000))  # legacy-поле, больше не используется
    error_message = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "provider": self.provider,
            "provider_payment_id": self.provider_payment_id,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "status": self.status,
            "checkout_url": self.checkout_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
