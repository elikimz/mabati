"""Regression tests for variation-aware order pricing and stock behavior."""
import time

import pytest


def _ts():
    return int(time.time() * 1000)


@pytest.fixture(scope="module")
def order_product(client, admin_headers):
    category_response = client.post(
        "/admin/categories", json={"name": f"OrderCat {_ts()}"}, headers=admin_headers
    )
    assert category_response.status_code == 201, category_response.text
    category_id = category_response.json()["id"]
    product_response = client.post(
        "/admin/products",
        json={
            "name": f"Order Product {_ts()}",
            "stock_quantity": 100,
            "category_id": category_id,
            "variations": [
                {"name": "30 Gauge", "gauge": "30 Gauge", "unit": "MTRS", "price": "2000.00"},
                {"name": "28 Gauge", "gauge": "28 Gauge", "unit": "MTRS", "price": "2400.00"},
            ],
        },
        headers=admin_headers,
    )
    assert product_response.status_code == 201, product_response.text
    product = product_response.json()
    # Keep historical orders and their product references intact for the session.
    # The disposable test database is removed automatically after the suite.
    yield product


def _selected_item(order_product: dict, quantity: int) -> dict:
    return {
        "product_id": order_product["id"],
        "variation_id": order_product["variations"][0]["id"],
        "quantity": quantity,
    }


def test_create_order_customer_with_selected_variation(client, customer_headers, order_product):
    response = client.post(
        "/orders",
        json={"items": [_selected_item(order_product, 2)], "shipping_address": "123 Nairobi St"},
        headers=customer_headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "pending"
    assert float(data["total_amount"]) == 4000.00
    assert data["items"][0]["variation_id"] == order_product["variations"][0]["id"]
    assert data["items"][0]["variation_snapshot"]["gauge"] == "30 Gauge"
    assert data["items"][0]["variation_snapshot"]["unit"] == "MTRS"


def test_multi_option_product_requires_variation(client, customer_headers, order_product):
    response = client.post(
        "/orders",
        json={"items": [{"product_id": order_product["id"], "quantity": 1}]},
        headers=customer_headers,
    )
    assert response.status_code == 422
    assert "Select a variation" in response.json()["detail"]


def test_create_order_unauthenticated(client, order_product):
    response = client.post("/orders", json={"items": [_selected_item(order_product, 1)]})
    assert response.status_code == 401


def test_legacy_single_price_order_stays_compatible(client, admin_headers, customer_headers):
    category_response = client.post(
        "/admin/categories", json={"name": f"LegacyOrderCat {_ts()}"}, headers=admin_headers
    )
    category_id = category_response.json()["id"]
    product_response = client.post(
        "/admin/products",
        json={
            "name": f"Legacy Order Product {_ts()}",
            "price_from": "750.00",
            "stock_quantity": 10,
            "category_id": category_id,
        },
        headers=admin_headers,
    )
    product = product_response.json()
    response = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
        headers=customer_headers,
    )
    assert response.status_code == 201, response.text
    item = response.json()["items"][0]
    assert item["variation_id"] is None
    assert float(item["unit_price"]) == 750.00
    assert item["variation_snapshot"] is None



def test_my_orders(client, customer_headers, order_product):
    client.post("/orders", json={"items": [_selected_item(order_product, 1)]}, headers=customer_headers)
    response = client.get("/orders/my-orders", headers=customer_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_admin_list_orders(client, admin_headers):
    response = client.get("/admin/orders", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_update_order_status(client, admin_headers, customer_headers, order_product):
    create_response = client.post("/orders", json={"items": [_selected_item(order_product, 1)]}, headers=customer_headers)
    assert create_response.status_code == 201, create_response.text
    order_id = create_response.json()["id"]
    response = client.put(f"/admin/orders/{order_id}/status", json={"status": "confirmed"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_cancel_order_restores_stock(client, admin_headers, customer_headers, order_product):
    product_before = client.get(f"/products/{order_product['id']}").json()
    stock_before = product_before["stock_quantity"]
    create_response = client.post("/orders", json={"items": [_selected_item(order_product, 3)]}, headers=customer_headers)
    assert create_response.status_code == 201, create_response.text
    order_id = create_response.json()["id"]
    cancel_response = client.put(f"/admin/orders/{order_id}/status", json={"status": "cancelled"}, headers=admin_headers)
    assert cancel_response.status_code == 200
    product_after = client.get(f"/products/{order_product['id']}").json()
    assert product_after["stock_quantity"] == stock_before


def test_order_insufficient_stock(client, customer_headers, order_product):
    response = client.post("/orders", json={"items": [_selected_item(order_product, 999999)]}, headers=customer_headers)
    assert response.status_code == 400


def test_admin_filter_orders_by_status(client, admin_headers):
    response = client.get("/admin/orders", params={"status": "pending"}, headers=admin_headers)
    assert response.status_code == 200
    assert all(order["status"] == "pending" for order in response.json())
