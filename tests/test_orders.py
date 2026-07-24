"""Tests for order endpoints."""
import time
import pytest


def _ts():
    return int(time.time() * 1000)


@pytest.fixture(scope="module")
def order_product(client, admin_headers):
    """Create a product for order tests."""
    cat_resp = client.post("/admin/categories", json={"name": f"OrderCat {_ts()}"}, headers=admin_headers)
    cat_id = cat_resp.json()["id"]
    prod_resp = client.post("/admin/products", json={
        "name": f"Order Product {_ts()}",
        "price": "2000.00",
        "stock_quantity": 100,
        "category_id": cat_id,
    }, headers=admin_headers)
    product = prod_resp.json()
    yield product
    client.delete(f"/admin/products/{product['id']}", headers=admin_headers)
    client.delete(f"/admin/categories/{cat_id}", headers=admin_headers)


def test_create_order_customer(client, customer_headers, order_product):
    resp = client.post("/orders", json={
        "items": [{"product_id": order_product["id"], "quantity": 2}],
        "shipping_address": "123 Nairobi St",
    }, headers=customer_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert float(data["total_amount"]) == 4000.00
    assert len(data["items"]) == 1
    return data["id"]


def test_create_order_unauthenticated(client, order_product):
    resp = client.post("/orders", json={
        "items": [{"product_id": order_product["id"], "quantity": 1}],
    })
    assert resp.status_code == 401


def test_my_orders(client, customer_headers, order_product):
    # Create an order first
    client.post("/orders", json={
        "items": [{"product_id": order_product["id"], "quantity": 1}],
    }, headers=customer_headers)
    resp = client.get("/orders/my-orders", headers=customer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_admin_list_orders(client, admin_headers):
    resp = client.get("/admin/orders", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_admin_update_order_status(client, admin_headers, customer_headers, order_product):
    # Create an order
    create_resp = client.post("/orders", json={
        "items": [{"product_id": order_product["id"], "quantity": 1}],
    }, headers=customer_headers)
    order_id = create_resp.json()["id"]

    # Update status
    resp = client.put(
        f"/admin/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


def test_cancel_order_restores_stock(client, admin_headers, customer_headers, order_product):
    # Check initial stock
    prod_before = client.get(f"/products/{order_product['id']}").json()
    stock_before = prod_before["stock_quantity"]

    # Place order
    create_resp = client.post("/orders", json={
        "items": [{"product_id": order_product["id"], "quantity": 3}],
    }, headers=customer_headers)
    order_id = create_resp.json()["id"]

    # Cancel order
    client.put(
        f"/admin/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=admin_headers,
    )

    # Stock should be restored
    prod_after = client.get(f"/products/{order_product['id']}").json()
    assert prod_after["stock_quantity"] == stock_before - 3 + 3


def test_order_insufficient_stock(client, customer_headers, order_product):
    resp = client.post("/orders", json={
        "items": [{"product_id": order_product["id"], "quantity": 999999}],
    }, headers=customer_headers)
    assert resp.status_code == 400


def test_admin_filter_orders_by_status(client, admin_headers):
    resp = client.get("/admin/orders", params={"status": "pending"}, headers=admin_headers)
    assert resp.status_code == 200
    for order in resp.json():
        assert order["status"] == "pending"
