"""Tests for product endpoints."""
import time
import pytest


def _ts():
    return int(time.time() * 1000)


@pytest.fixture(scope="module")
def category_id(client, admin_headers):
    """Create a temporary category for product tests."""
    resp = client.post("/admin/categories", json={"name": f"ProdTestCat {_ts()}"}, headers=admin_headers)
    assert resp.status_code == 201
    cat_id = resp.json()["id"]
    yield cat_id
    client.delete(f"/admin/categories/{cat_id}", headers=admin_headers)


@pytest.fixture(scope="module")
def sample_product(client, admin_headers, category_id):
    """Create a sample product for tests."""
    payload = {
        "name": f"Box Profile Sheet {_ts()}",
        "description": "Galvanised roofing sheet",
        "brand": "Mabati Rolling Mills",
        "price": "1500.00",
        "color": "Charcoal Grey",
        "gauge": "0.3mm",
        "length": 3.0,
        "width": 0.9,
        "profile": "Box Profile",
        "stock_quantity": 100,
        "category_id": category_id,
    }
    resp = client.post("/admin/products", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    product = resp.json()
    yield product
    client.delete(f"/admin/products/{product['id']}", headers=admin_headers)


def test_list_products_public(client):
    resp = client.get("/products")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_product_by_id(client, sample_product):
    resp = client.get(f"/products/{sample_product['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_product["id"]


def test_get_nonexistent_product(client):
    resp = client.get("/products/999999")
    assert resp.status_code == 404


def test_search_products(client, sample_product):
    resp = client.get("/products", params={"search": "Box Profile"})
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert sample_product["id"] in ids


def test_filter_by_color(client, sample_product):
    resp = client.get("/products", params={"color": "Charcoal"})
    assert resp.status_code == 200
    for p in resp.json():
        assert "charcoal" in p["color"].lower()


def test_filter_by_gauge(client, sample_product):
    resp = client.get("/products", params={"gauge": "0.3mm"})
    assert resp.status_code == 200


def test_create_product_no_auth(client, category_id):
    resp = client.post("/admin/products", json={
        "name": "Unauth Product",
        "price": "100.00",
        "stock_quantity": 10,
        "category_id": category_id,
    })
    assert resp.status_code == 401


def test_update_product(client, admin_headers, sample_product):
    resp = client.put(
        f"/admin/products/{sample_product['id']}",
        json={"price": "1800.00"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert float(resp.json()["price"]) == 1800.00


def test_create_product_invalid_category(client, admin_headers):
    resp = client.post("/admin/products", json={
        "name": "Bad Product",
        "price": "100.00",
        "stock_quantity": 5,
        "category_id": 999999,
    }, headers=admin_headers)
    assert resp.status_code == 404
