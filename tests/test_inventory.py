"""Tests for inventory endpoints."""
import time
import pytest


def _ts():
    return int(time.time() * 1000)


@pytest.fixture(scope="module")
def inv_product(client, admin_headers):
    """Create a product for inventory tests."""
    cat_resp = client.post("/admin/categories", json={"name": f"InvCat {_ts()}"}, headers=admin_headers)
    cat_id = cat_resp.json()["id"]
    prod_resp = client.post("/admin/products", json={
        "name": f"Inv Product {_ts()}",
        "price_from": "500.00",
        "stock_quantity": 50,
        "category_id": cat_id,
    }, headers=admin_headers)
    product = prod_resp.json()
    # Inventory logs retain product references; suite-level database cleanup is sufficient.
    yield product


def test_get_low_stock_overview(client, admin_headers):
    resp = client.get("/admin/inventory/", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_adjust_stock_restock(client, admin_headers, inv_product):
    resp = client.post(
        f"/admin/inventory/{inv_product['id']}/adjust",
        json={"change": 20, "reason": "restock", "note": "Weekly restock"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["change"] == 20
    assert data["reason"] == "restock"


def test_adjust_stock_removal(client, admin_headers, inv_product):
    resp = client.post(
        f"/admin/inventory/{inv_product['id']}/adjust",
        json={"change": -10, "reason": "adjustment"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["change"] == -10


def test_adjust_stock_insufficient(client, admin_headers, inv_product):
    resp = client.post(
        f"/admin/inventory/{inv_product['id']}/adjust",
        json={"change": -99999},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_get_inventory_logs(client, admin_headers, inv_product):
    resp = client.get(f"/admin/inventory/{inv_product['id']}/logs", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_inventory_requires_auth(client, inv_product):
    resp = client.get("/admin/inventory/")
    assert resp.status_code == 401


def test_inventory_customer_forbidden(client, customer_headers, inv_product):
    resp = client.get("/admin/inventory/", headers=customer_headers)
    assert resp.status_code == 403
