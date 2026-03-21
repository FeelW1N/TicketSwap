from flask import Flask
from app.config import Config
from app.extensions import db, jwt, migrate


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Celery
    from app.tasks.celery_app import make_celery
    celery = make_celery(app)
    app.extensions["celery"] = celery

    # Blueprints
    from app.routes import auth_bp, listings_bp, orders_bp, payments_bp, tickets_bp, events_bp, wallet_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(wallet_bp)

    # Seed command
    from seed import register_seed_command
    register_seed_command(app)

    # Health check
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
