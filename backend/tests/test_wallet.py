"""Unit-тесты: кошелёк продавца."""
import uuid
import pytest
from app.extensions import db
from app.models.event import Event
from datetime import datetime, timezone


@pytest.fixture
def event(app):
    with app.app_context():
        e = Event(
            title="Wallet Test Event",
            event_date=datetime(2026, 8, 1, 19, 0, tzinfo=timezone.utc),
            organizer_id="org-wallet",
            city="Moscow",
        )
        db.session.add(e)
        db.session.commit()
        yield e


@pytest.fixture
def seller_headers(client):
    """Уникальный продавец на каждый тест — чтобы баланс не накапливался."""
    uid = uuid.uuid4().hex[:8]
    creds = {"email": f"w_seller_{uid}@example.com", "password": "password123", "full_name": "Wallet Seller"}
    resp = client.post("/auth/register", json=creds)
    return {"Authorization": f"Bearer {resp.json['access_token']}"}


@pytest.fixture
def buyer_headers(client):
    uid = uuid.uuid4().hex[:8]
    creds = {"email": f"w_buyer_{uid}@example.com", "password": "password123", "full_name": "Wallet Buyer"}
    resp = client.post("/auth/register", json=creds)
    return {"Authorization": f"Bearer {resp.json['access_token']}"}


def _sell_and_buy(client, seller_headers, buyer_headers, event, app, price=2000):
    """Вспомогательная функция: продавец создаёт листинг, покупатель покупает."""
    with app.app_context():
        ev = Event.query.filter_by(organizer_id="org-wallet").first()
        listing_resp = client.post("/listings", json={
            "event_id": str(ev.id), "price": price,
            "external_ticket_id": f"TKT-W-{uuid.uuid4().hex[:6]}",
            "organizer_id": "org-wallet",
        }, headers=seller_headers)
    listing_id = listing_resp.json["id"]
    order_resp = client.post("/orders", json={"listing_id": listing_id}, headers=buyer_headers)
    client.post("/payments/create", json={"order_id": order_resp.json["id"]}, headers=buyer_headers)
    return order_resp.json


# ── GET /wallet/balance ───────────────────────────────────────────────────────

def test_get_balance_unauthenticated(client):
    resp = client.get("/wallet/balance")
    assert resp.status_code == 401


def test_get_balance_initial_zero(client, seller_headers):
    resp = client.get("/wallet/balance", headers=seller_headers)
    assert resp.status_code == 200
    assert resp.json["balance"] == 0.0


def test_balance_increases_after_sale(client, seller_headers, buyer_headers, event, app):
    _sell_and_buy(client, seller_headers, buyer_headers, event, app, price=1000)
    resp = client.get("/wallet/balance", headers=seller_headers)
    assert resp.json["balance"] == pytest.approx(950.0, abs=0.01)


# ── POST /wallet/withdraw ─────────────────────────────────────────────────────

def test_withdraw_unauthenticated(client):
    resp = client.post("/wallet/withdraw", json={"amount": 100})
    assert resp.status_code == 401


def test_withdraw_success(client, seller_headers, buyer_headers, event, app):
    _sell_and_buy(client, seller_headers, buyer_headers, event, app, price=2000)
    bal_before = client.get("/wallet/balance", headers=seller_headers).json["balance"]

    resp = client.post("/wallet/withdraw", json={"amount": 500}, headers=seller_headers)
    assert resp.status_code == 200
    assert resp.json["withdrawn"] == 500.0
    assert abs(resp.json["balance"] - (bal_before - 500)) < 0.01


def test_withdraw_insufficient_balance(client, seller_headers):
    resp = client.post("/wallet/withdraw", json={"amount": 999999}, headers=seller_headers)
    assert resp.status_code == 400
    assert "insufficient" in resp.json["error"]


def test_withdraw_below_minimum(client, seller_headers, buyer_headers, event, app):
    _sell_and_buy(client, seller_headers, buyer_headers, event, app, price=2000)
    resp = client.post("/wallet/withdraw", json={"amount": 50}, headers=seller_headers)
    assert resp.status_code == 400
    assert "minimum" in resp.json["error"]


def test_withdraw_zero_amount(client, seller_headers):
    resp = client.post("/wallet/withdraw", json={"amount": 0}, headers=seller_headers)
    assert resp.status_code == 400


def test_withdraw_negative_amount(client, seller_headers):
    resp = client.post("/wallet/withdraw", json={"amount": -100}, headers=seller_headers)
    assert resp.status_code == 400


def test_withdraw_missing_amount(client, seller_headers):
    resp = client.post("/wallet/withdraw", json={}, headers=seller_headers)
    assert resp.status_code == 400


def test_withdraw_reduces_balance(client, seller_headers, buyer_headers, event, app):
    _sell_and_buy(client, seller_headers, buyer_headers, event, app, price=2000)
    bal = client.get("/wallet/balance", headers=seller_headers).json["balance"]
    withdraw_amount = 100.0
    client.post("/wallet/withdraw", json={"amount": withdraw_amount}, headers=seller_headers)
    new_bal = client.get("/wallet/balance", headers=seller_headers).json["balance"]
    assert abs(new_bal - (bal - withdraw_amount)) < 0.01


def test_platform_fee_5_percent(client, seller_headers, buyer_headers, event, app):
    """Проверяем что комиссия ровно 5%."""
    _sell_and_buy(client, seller_headers, buyer_headers, event, app, price=1000)
    bal = client.get("/wallet/balance", headers=seller_headers).json["balance"]
    assert bal == pytest.approx(1000 * 0.95, abs=0.01)
