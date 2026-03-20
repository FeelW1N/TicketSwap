"""Unit-тесты: листинги, бизнес-правила цены."""
import pytest
from app.extensions import db
from app.models.event import Event
from datetime import datetime, timezone


@pytest.fixture
def event(app):
    with app.app_context():
        e = Event(
            title="Test Concert",
            event_date=datetime(2026, 6, 1, 19, 0, tzinfo=timezone.utc),
            organizer_id="org-1",
            city="Moscow",
        )
        db.session.add(e)
        db.session.commit()
        yield e


def test_create_listing_success(client, auth_headers, event, app):
    with app.app_context():
        from app.models.event import Event as E
        ev = E.query.first()
        resp = client.post("/listings", json={
            "event_id": str(ev.id),
            "price": 1500,
            "external_ticket_id": "TKT-001",
            "organizer_id": "org-1",
            "seat_info": "A1",
        }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json
    assert data["status"] == "ACTIVE"
    assert data["price"] == 1500.0


def test_create_listing_price_exceeds_markup(client, auth_headers, event, app):
    """Цена > 120% от face_value (1500) → 422."""
    with app.app_context():
        from app.models.event import Event as E
        ev = E.query.first()
        resp = client.post("/listings", json={
            "event_id": str(ev.id),
            "price": 9999,  # mock face_value=1500 → max=1800
            "external_ticket_id": "TKT-002",
            "organizer_id": "org-1",
        }, headers=auth_headers)
    assert resp.status_code == 422
    assert "markup" in resp.json["error"]


def test_get_listings(client):
    resp = client.get("/listings")
    assert resp.status_code == 200
    assert "items" in resp.json


def test_create_listing_unauthenticated(client):
    resp = client.post("/listings", json={"event_id": "x", "price": 100, "external_ticket_id": "y", "organizer_id": "z"})
    assert resp.status_code == 401
