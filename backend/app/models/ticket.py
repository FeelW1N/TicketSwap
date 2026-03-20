import uuid
from datetime import datetime, timezone
from app.extensions import db


class TicketStatus:
    ACTIVE = "ACTIVE"
    REISSUED = "REISSUED"
    CANCELLED = "CANCELLED"


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_ticket_id = db.Column(db.String(255), nullable=False)
    organizer_id = db.Column(db.String(255), nullable=False)
    owner_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.String(36), db.ForeignKey("events.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=TicketStatus.ACTIVE)
    seat_info = db.Column(db.String(255))  # сектор, ряд, место
    face_value = db.Column(db.Numeric(10, 2))  # исходная цена
    s3_key = db.Column(db.String(500))  # ключ файла в S3
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    listings = db.relationship("Listing", backref="ticket", lazy="dynamic")
    reissue_requests = db.relationship("ReissueRequest", backref="ticket", lazy="dynamic",
                                       foreign_keys="ReissueRequest.ticket_id")

    __table_args__ = (
        # уникальность external_ticket_id в рамках конкретного организатора
        db.UniqueConstraint("organizer_id", "external_ticket_id", name="uq_ticket_organizer_external"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "external_ticket_id": self.external_ticket_id,
            "organizer_id": self.organizer_id,
            "owner_user_id": str(self.owner_user_id),
            "event_id": str(self.event_id),
            "status": self.status,
            "seat_info": self.seat_info,
            "face_value": float(self.face_value) if self.face_value else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
