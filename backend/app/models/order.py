import uuid
from datetime import datetime, timezone
from app.extensions import db


class OrderStatus:
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = db.Column(db.String(36), db.ForeignKey("listings.id"), nullable=False)
    buyer_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default=OrderStatus.PENDING_PAYMENT)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    cancel_reason = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    payment = db.relationship("Payment", backref="order", uselist=False)
    reissue_request = db.relationship("ReissueRequest", backref="order", uselist=False,
                                      foreign_keys="ReissueRequest.order_id")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "listing_id": str(self.listing_id),
            "buyer_user_id": str(self.buyer_user_id),
            "status": self.status,
            "amount": float(self.amount) if self.amount else None,
            "cancel_reason": self.cancel_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
