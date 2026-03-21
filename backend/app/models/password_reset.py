import secrets
import uuid
from datetime import datetime, timedelta
from app.extensions import db

TOKEN_EXPIRY_HOURS = 1


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    # Naive UTC — совместимо и с SQLite, и с PostgreSQL
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="reset_tokens")

    @classmethod
    def create_for_user(cls, user_id: str) -> "PasswordResetToken":
        token = secrets.token_urlsafe(48)
        expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        return cls(user_id=user_id, token=token, expires_at=expires_at)

    @property
    def is_valid(self) -> bool:
        return not self.used and datetime.utcnow() < self.expires_at
