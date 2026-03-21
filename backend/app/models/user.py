import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(20), nullable=False, default="user")  # user, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    listings = db.relationship("Listing", backref="seller", lazy="dynamic", foreign_keys="Listing.seller_user_id")
    orders = db.relationship("Order", backref="buyer", lazy="dynamic", foreign_keys="Order.buyer_user_id")
    owned_tickets = db.relationship("Ticket", backref="owner", lazy="dynamic", foreign_keys="Ticket.owner_user_id")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "balance": float(self.balance) if self.balance is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
