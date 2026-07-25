"""Regression tests for public and admin product variation endpoints."""
import time

import pytest


def _ts():
    return int(time.time() * 1000)


def _variation_payload(variation: dict, *, price: str | None = None) -> dict:
    """Keep only writable fields when sending an existing variation in an upsert."""
    fields = {
        "id", "name", "sku", "gauge", "size_label", "length", "width", "color",
        "unit", "price", "discount_price", "specifications", "sort_order",
        "is_available", "is_active",
    }
    payload = {key: value for key, value in variation.items() if key in fields}
    if price is not None:
        payload["price"] = price
    return payload


@pytest.fixture(scope="module")
def category_id(client, admin_headers):
    response = client.post(
        "/admin/categories", json={"name": f"ProdTestCat {_ts()}"}, headers=admin_headers
    )
    assert response.status_code == 201
    category = response.json()["id"]
    yield category
    client.delete(f"/admin/categories/{category}", headers=admin_headers)


@pytest.fixture(scope="module")
def sample_product(client, admin_headers, category_id):
    """Create a product family with independently priced gauges."""
    response = client.post(
        "/admin/products",
        json={
            "name": f"Box Profile Sheet {_ts()}",
            "description": "Galvanised roofing sheet",
            "brand": "Mabati Rolling Mills",
            "color": "Charcoal Grey",
            "profile": "Box Profile",
            "stock_quantity": 100,
            "category_id": category_id,
            "variations": [
                {
                    "name": "30 Gauge",
                    "gauge": "30 Gauge",
                    "unit": "MTRS",
                    "price": "1500.00",
                    "specifications": {"Profile": "Box Profile"},
                },
                {
                    "name": "28 Gauge",
                    "gauge": "28 Gauge",
                    "unit": "MTRS",
                    "price": "1800.00",
                    "specifications": {"Profile": "Box Profile"},
                },
            ],
        },
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    product = response.json()
    yield product
    client.delete(f"/admin/products/{product['id']}", headers=admin_headers)


def test_list_products_public(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_product_by_id_includes_priced_variations(client, sample_product):
    response = client.get(f"/products/{sample_product['id']}")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == sample_product["id"]
    assert product["price_from"] == "1500.00"
    assert product["price_to"] == "1800.00"
    assert [variation["gauge"] for variation in product["variations"]] == ["30 Gauge", "28 Gauge"]
    assert product["variations"][0]["effective_price"] == "1500.00"


def test_get_nonexistent_product(client):
    assert client.get("/products/999999").status_code == 404


def test_search_products(client, sample_product):
    response = client.get("/products", params={"search": "Box Profile"})
    assert response.status_code == 200
    assert sample_product["id"] in [product["id"] for product in response.json()]


def test_filter_by_product_and_variation_attributes(client, sample_product):
    color_response = client.get("/products", params={"color": "Charcoal"})
    assert color_response.status_code == 200
    assert sample_product["id"] in [product["id"] for product in color_response.json()]

    gauge_response = client.get("/products", params={"gauge": "28 Gauge"})
    assert gauge_response.status_code == 200
    assert sample_product["id"] in [product["id"] for product in gauge_response.json()]


def test_create_product_no_auth(client, category_id):
    response = client.post(
        "/admin/products",
        json={"name": "Unauth Product", "price_from": "100.00", "stock_quantity": 10, "category_id": category_id},
    )
    assert response.status_code == 401


def test_update_one_variation_price_recalculates_range(client, admin_headers, sample_product):
    variations = sample_product["variations"]
    response = client.put(
        f"/admin/products/{sample_product['id']}",
        json={"variations": [_variation_payload(variations[0], price="1600.00"), _variation_payload(variations[1])]},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    product = response.json()
    assert product["price_from"] == "1600.00"
    assert product["price_to"] == "1800.00"
    assert product["variations"][0]["price"] == "1600.00"


def test_create_legacy_single_price_product(client, admin_headers, category_id):
    response = client.post(
        "/admin/products",
        json={
            "name": f"Legacy Flashing {_ts()}",
            "price_from": "100.00",
            "stock_quantity": 5,
            "category_id": category_id,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    product = response.json()
    assert product["price_from"] == "100.00"
    assert product["variations"] == []
    client.delete(f"/admin/products/{product['id']}", headers=admin_headers)


def test_create_product_invalid_category(client, admin_headers):
    response = client.post(
        "/admin/products",
        json={"name": "Bad Product", "price_from": "100.00", "stock_quantity": 5, "category_id": 999999},
        headers=admin_headers,
    )
    assert response.status_code == 404
