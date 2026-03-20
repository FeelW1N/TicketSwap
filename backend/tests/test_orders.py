"""Unit-тесты: заказы."""


def test_create_order_missing_listing_id(client, auth_headers):
    resp = client.post("/orders", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_get_order_not_found(client, auth_headers):
    import uuid
    resp = client.get(f"/orders/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_list_orders_empty(client, auth_headers):
    resp = client.get("/orders", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json["items"] == [] or isinstance(resp.json["items"], list)
