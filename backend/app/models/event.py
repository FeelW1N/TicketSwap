import uuid
from datetime import datetime, timezone
from app.extensions import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    venue = db.Column(db.String(500))
    city = db.Column(db.String(255))
    event_date = db.Column(db.DateTime(timezone=True), nullable=False)
    organizer_id = db.Column(db.String(255), nullable=False)  # ID организатора (внешняя система)
    external_event_id = db.Column(db.String(255))  # ID события в системе организатора
    category = db.Column(db.String(100))  # concert, sport, theatre, etc.
    image_url = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    tickets = db.relationship("Ticket", backref="event", lazy="dynamic")
    listings = db.relationship("Listing", backref="event", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("organizer_id", "external_event_id", name="uq_event_organizer_external"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "venue": self.venue,
            "city": self.city,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "organizer_id": self.organizer_id,
            "external_event_id": self.external_event_id,
            "category": self.category,
            "image_url": self.image_url,
        }
