"""Unit-тесты: заказы и полный цикл покупки."""
import uuid
import pytest
from app.extensions import db
from app.models.event import Event
from datetime import datetime, timezone


@pytest.fixture
def event(app):
    with app.app_context():
        e = Event(
            title="Order Test Concert",
            event_date=datetime(2026, 7, 1, 19, 0, tzinfo=timezone.utc),
            organizer_id="org-orders",
            city="Moscow",
        )
        db.session.add(e)
        db.session.commit()
        yield e


@pytest.fixture
def seller_headers(client):
    creds = {"email": "seller_orders@example.com", "password": "password123", "full_name": "Seller"}
    resp = client.post("/auth/register", json=creds)
    if resp.status_code == 409:
        resp = client.post("/auth/login", json={"email": creds["email"], "password": creds["password"]})
    return {"Authorization": f"Bearer {resp.json['access_token']}"}


@pytest.fixture
def buyer_headers(client):
    creds = {"email": "buyer_orders@example.com", "password": "password123", "full_name": "Buyer"}
    resp = client.post("/auth/register", json=creds)
    if resp.status_code == 409:
        resp = client.post("/auth/login", json={"email": creds["email"], "password": creds["password"]})
    return {"Authorization": f"Bearer {resp.json['access_token']}"}


@pytest.fixture
def active_listing(client, seller_headers, event, app):
    """Создаёт активный листинг и возвращает его данные."""
    with app.app_context():
        ev = Event.query.filter_by(organizer_id="org-orders").first()
        resp = client.post("/listings", json={
            "event_id": str(ev.id), "price": 2000,
            "external_ticket_id": f"TKT-ORD-{uuid.uuid4().hex[:6]}",
            "organizer_id": "org-orders",
        }, headers=seller_headers)
    return resp.json


# ── Создание заказа ──────────────────────────────────────────────────────────

def test_create_order_missing_listing_id(client, auth_headers):
    resp = client.post("/orders", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_create_order_unauthenticated(client, active_listing):
    resp = client.post("/orders", json={"listing_id": active_listing["id"]})
    assert resp.status_code == 401


def test_create_order_listing_not_found(client, buyer_headers):
    resp = client.post("/orders", json={"listing_id": str(uuid.uuid4())}, headers=buyer_headers)
    assert resp.status_code == 404


def test_create_order_success(client, buyer_headers, active_listing):
    resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    assert resp.status_code == 201
    assert resp.json["status"] == "PENDING_PAYMENT"
    assert resp.json["amount"] == 2000.0


def test_seller_cannot_buy_own_listing(client, seller_headers, active_listing):
    """Продавец не может купить свой же билет."""
    resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=seller_headers)
    assert resp.status_code == 422


def test_create_order_idempotent(client, buyer_headers, active_listing):
    """Повторный заказ на тот же листинг → 409 (уже заблокирован)."""
    client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    assert resp.status_code == 409


# ── Получение заказов ────────────────────────────────────────────────────────

def test_get_order_not_found(client, auth_headers):
    resp = client.get(f"/orders/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_get_order_forbidden(client, seller_headers, buyer_headers, active_listing):
    """Продавец не может видеть заказ покупателя."""
    order_resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    order_id = order_resp.json["id"]
    resp = client.get(f"/orders/{order_id}", headers=seller_headers)
    assert resp.status_code == 403


def test_get_order_success(client, buyer_headers, active_listing):
    order_resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    order_id = order_resp.json["id"]
    resp = client.get(f"/orders/{order_id}", headers=buyer_headers)
    assert resp.status_code == 200
    assert resp.json["id"] == order_id


def test_list_orders_empty(client, auth_headers):
    resp = client.get("/orders", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json["items"], list)


def test_list_orders_unauthenticated(client):
    resp = client.get("/orders")
    assert resp.status_code == 401


# ── Полный цикл: заказ → оплата → переоформление ────────────────────────────

def test_full_purchase_flow(client, buyer_headers, active_listing, app):
    """DEBUG auto-confirm: создаём заказ → платим → Order=PAID → Reissue=SUCCESS."""
    # Создаём заказ
    order_resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    assert order_resp.status_code == 201
    order_id = order_resp.json["id"]
    assert order_resp.json["status"] == "PENDING_PAYMENT"

    # Оплата (DEBUG auto-confirm)
    pay_resp = client.post("/payments/create", json={"order_id": order_id}, headers=buyer_headers)
    assert pay_resp.status_code == 201
    assert pay_resp.json["payment"]["status"] == "CONFIRMED"
    assert pay_resp.json["payment"]["provider"] == "debug"

    # Проверяем статус заказа
    order_resp2 = client.get(f"/orders/{order_id}", headers=buyer_headers)
    assert order_resp2.json["status"] == "PAID"

    # Переоформление запустилось — reissue создан (статус зависит от доступности mock organizer)
    reissue = order_resp2.json.get("reissue")
    assert reissue is not None
    assert reissue["status"] in ("PENDING", "SUCCESS", "FAILED")


def test_payment_wrong_user(client, seller_headers, buyer_headers, active_listing):
    """Продавец не может оплатить чужой заказ."""
    order_resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    order_id = order_resp.json["id"]
    resp = client.post("/payments/create", json={"order_id": order_id}, headers=seller_headers)
    assert resp.status_code == 403


def test_payment_already_paid(client, buyer_headers, active_listing):
    """Повторная оплата уже оплаченного заказа → 409."""
    order_resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    order_id = order_resp.json["id"]
    client.post("/payments/create", json={"order_id": order_id}, headers=buyer_headers)
    resp = client.post("/payments/create", json={"order_id": order_id}, headers=buyer_headers)
    assert resp.status_code == 409


def test_seller_balance_credited_after_purchase(client, seller_headers, buyer_headers, active_listing, app):
    """После покупки баланс продавца должен вырасти на 95% от цены."""
    # Баланс до
    bal_before = client.get("/wallet/balance", headers=seller_headers).json["balance"]

    order_resp = client.post("/orders", json={"listing_id": active_listing["id"]}, headers=buyer_headers)
    client.post("/payments/create", json={"order_id": order_resp.json["id"]}, headers=buyer_headers)

    # Баланс после
    bal_after = client.get("/wallet/balance", headers=seller_headers).json["balance"]
    expected_payout = 2000 * 0.95
    assert abs(bal_after - bal_before - expected_payout) < 0.01
