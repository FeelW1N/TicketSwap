import uuid
from datetime import datetime, timezone
from app.extensions import db


class ListingStatus:
    ACTIVE = "ACTIVE"
    SOLD = "SOLD"
    BLOCKED = "BLOCKED"


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False)
    seller_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default=ListingStatus.ACTIVE, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    orders = db.relationship("Order", backref="listing", lazy="dynamic")

    def to_dict(self, include_ticket: bool = False, include_event: bool = False) -> dict:
        data = {
            "id": str(self.id),
            "ticket_id": str(self.ticket_id),
            "event_id": str(self.event_id),
            "seller_user_id": str(self.seller_user_id),
            "price": float(self.price) if self.price else None,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_event and self.event:
            data["event"] = self.event.to_dict()
        if include_ticket and self.ticket:
            data["ticket"] = {
                "seat_info": self.ticket.seat_info,
                "face_value": float(self.ticket.face_value) if self.ticket.face_value else None,
            }
        return data
