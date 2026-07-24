"""Tests for category endpoints."""
import time
import pytest


def _cat_name():
    return f"Test Category {int(time.time() * 1000)}"


def test_list_categories_public(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_category_admin(client, admin_headers):
    name = _cat_name()
    resp = client.post("/admin/categories", json={"name": name, "description": "Test"}, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == name
    assert data["is_active"] is True
    # Cleanup
    client.delete(f"/admin/categories/{data['id']}", headers=admin_headers)


def test_create_category_no_auth(client):
    resp = client.post("/admin/categories", json={"name": _cat_name()})
    assert resp.status_code == 401


def test_create_category_customer_forbidden(client, customer_headers):
    resp = client.post("/admin/categories", json={"name": _cat_name()}, headers=customer_headers)
    assert resp.status_code == 403


def test_update_category(client, admin_headers):
    name = _cat_name()
    create_resp = client.post("/admin/categories", json={"name": name}, headers=admin_headers)
    cat_id = create_resp.json()["id"]
    new_name = _cat_name()
    resp = client.put(f"/admin/categories/{cat_id}", json={"name": new_name}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == new_name
    client.delete(f"/admin/categories/{cat_id}", headers=admin_headers)


def test_delete_category(client, admin_headers):
    create_resp = client.post("/admin/categories", json={"name": _cat_name()}, headers=admin_headers)
    cat_id = create_resp.json()["id"]
    resp = client.delete(f"/admin/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_update_nonexistent_category(client, admin_headers):
    resp = client.put("/admin/categories/999999", json={"name": "NonExistent"}, headers=admin_headers)
    assert resp.status_code == 404
