"""Unit-тесты: листинги, бизнес-правила цены."""

import uuid
import pytest
from app.extensions import db
from app.models.event import Event
from datetime import datetime, timezone


@pytest.fixture
def event(app):
    with app.app_context():
        e = Event.query.filter_by(
            organizer_id="redkassa", external_event_id="rk-bi2-2026"
        ).first()
        if not e:
            e = Event(
                title="Би-2: Горизонт событий",
                event_date=datetime(2026, 6, 1, 19, 0, tzinfo=timezone.utc),
                organizer_id="redkassa",
                external_event_id="rk-bi2-2026",
                city="Moscow",
            )
            db.session.add(e)
            db.session.commit()
        yield e


@pytest.fixture
def second_user_headers(client):
    creds = {
        "email": "other@example.com",
        "password": "password123",
        "full_name": "Other User",
    }
    resp = client.post("/auth/register", json=creds)
    if resp.status_code == 409:
        resp = client.post(
            "/auth/login", json={"email": creds["email"], "password": creds["password"]}
        )
    token = resp.json["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _payload(event_id, ext_id="TKT-001", price=1500):
    return {
        "event_id": str(event_id),
        "price": price,
        "external_ticket_id": ext_id,
        "organizer_id": "redkassa",
        "seat_info": "A1",
    }


# ── Создание ──────────────────────────────────────────────────────────────────


def test_create_listing_success(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        resp = client.post("/listings", json=_payload(ev.id), headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json["status"] == "ACTIVE"
    assert resp.json["price"] == 1500.0


def test_create_listing_unauthenticated(client, event, app):
    with app.app_context():
        ev = Event.query.first()
        resp = client.post("/listings", json=_payload(ev.id))
    assert resp.status_code == 401


def test_create_listing_missing_event_id(client, auth_headers):
    resp = client.post(
        "/listings",
        json={"price": 100, "external_ticket_id": "x", "organizer_id": "y"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "external_event_id is required"


def test_create_listing_missing_price(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        payload = _payload(ev.id)
        del payload["price"]
        resp = client.post("/listings", json=payload, headers=auth_headers)
    assert resp.status_code == 400


def test_create_listing_invalid_price_string(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        payload = _payload(ev.id)
        payload["price"] = "not-a-number"
        resp = client.post("/listings", json=payload, headers=auth_headers)
    assert resp.status_code == 400
    assert "number" in resp.json["error"]


def test_create_listing_negative_price(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        resp = client.post(
            "/listings", json=_payload(ev.id, price=-100), headers=auth_headers
        )
    assert resp.status_code == 400
    assert "positive" in resp.json["error"]


def test_create_listing_zero_price(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        resp = client.post(
            "/listings", json=_payload(ev.id, price=0), headers=auth_headers
        )
    assert resp.status_code == 400
    assert "positive" in resp.json["error"]


def test_create_listing_high_price_debug_mode(client, auth_headers, event, app):
    """В DEBUG=True наценка не ограничена — любая цена проходит."""
    with app.app_context():
        ev = Event.query.first()
        resp = client.post(
            "/listings",
            json=_payload(ev.id, ext_id="TKT-HIGH", price=99999),
            headers=auth_headers,
        )
    assert resp.status_code == 201


def test_create_listing_event_not_found(client, auth_headers):
    resp = client.post(
        "/listings",
        json={
            "external_event_id": "missing-event",
            "price": 1000,
            "external_ticket_id": "TKT-X",
            "organizer_id": "redkassa",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json["error"] == "selected event was not found at organizer"


def test_create_listing_event_and_organizer_mismatch(client, auth_headers, event):
    resp = client.post(
        "/listings",
        json={
            "event_id": str(event.id),
            "price": 1000,
            "external_ticket_id": "TKT-MISMATCH",
            "organizer_id": "qtickets",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert resp.json["error"] == "selected event belongs to a different organizer"


def test_create_listing_duplicate_ticket(client, auth_headers, event, app):
    """Повторный листинг с тем же external_ticket_id → 409."""
    with app.app_context():
        ev = Event.query.first()
        payload = _payload(ev.id, ext_id="TKT-DUP")
        client.post("/listings", json=payload, headers=auth_headers)
        resp = client.post("/listings", json=payload, headers=auth_headers)
    assert resp.status_code == 409


def test_create_listing_with_external_event_id(client, auth_headers):
    resp = client.post(
        "/listings",
        json={
            "organizer_id": "redkassa",
            "external_event_id": "rk-bi2-2026",
            "external_ticket_id": "RK-BI2-1001",
            "price": 5500,
            "seat_info": "Сектор A, ряд 3, место 15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json["event"]["organizer_id"] == "redkassa"


def test_list_organizers(client):
    resp = client.get("/organizers")
    assert resp.status_code == 200
    assert len(resp.json["items"]) >= 3


def test_list_organizer_events(client):
    resp = client.get("/organizers/redkassa/events")
    assert resp.status_code == 200
    event = next(event for event in resp.json["items"] if event["id"] == "rk-bi2-2026")
    assert event["sample_ticket_ids"][0] == "RK-BI2-1001"


# ── Получение ────────────────────────────────────────────────────────────────


def test_get_listings(client):
    resp = client.get("/listings")
    assert resp.status_code == 200
    assert "items" in resp.json
    assert "total" in resp.json
    assert "page" in resp.json


def test_get_listings_pagination(client):
    resp = client.get("/listings?page=1&per_page=5")
    assert resp.status_code == 200
    assert len(resp.json["items"]) <= 5


def test_get_listing_by_id(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        create_resp = client.post(
            "/listings", json=_payload(ev.id, ext_id="TKT-GET"), headers=auth_headers
        )
    listing_id = create_resp.json["id"]
    resp = client.get(f"/listings/{listing_id}")
    assert resp.status_code == 200
    assert resp.json["id"] == listing_id


def test_get_listing_not_found(client):
    resp = client.get(f"/listings/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Отмена ───────────────────────────────────────────────────────────────────


def test_cancel_listing_success(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        create_resp = client.post(
            "/listings", json=_payload(ev.id, ext_id="TKT-CANCEL"), headers=auth_headers
        )
    listing_id = create_resp.json["id"]
    resp = client.delete(f"/listings/{listing_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_cancel_listing_forbidden(
    client, auth_headers, second_user_headers, event, app
):
    """Чужой пользователь не может отменить листинг."""
    with app.app_context():
        ev = Event.query.first()
        create_resp = client.post(
            "/listings", json=_payload(ev.id, ext_id="TKT-FORBID"), headers=auth_headers
        )
    listing_id = create_resp.json["id"]
    resp = client.delete(f"/listings/{listing_id}", headers=second_user_headers)
    assert resp.status_code == 403


def test_cancel_listing_twice(client, auth_headers, event, app):
    """Повторная отмена уже отменённого листинга → 409."""
    with app.app_context():
        ev = Event.query.first()
        create_resp = client.post(
            "/listings", json=_payload(ev.id, ext_id="TKT-TWICE"), headers=auth_headers
        )
    listing_id = create_resp.json["id"]
    client.delete(f"/listings/{listing_id}", headers=auth_headers)
    resp = client.delete(f"/listings/{listing_id}", headers=auth_headers)
    assert resp.status_code == 409


def test_cancel_listing_unauthenticated(client, auth_headers, event, app):
    with app.app_context():
        ev = Event.query.first()
        create_resp = client.post(
            "/listings", json=_payload(ev.id, ext_id="TKT-NOAUTH"), headers=auth_headers
        )
    listing_id = create_resp.json["id"]
    resp = client.delete(f"/listings/{listing_id}")
    assert resp.status_code == 401
