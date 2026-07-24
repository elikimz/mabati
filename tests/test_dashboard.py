"""Tests for admin dashboard endpoint."""
import pytest


def test_dashboard_admin(client, admin_headers):
    resp = client.get("/admin/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_products" in data
    assert "total_customers" in data
    assert "total_orders" in data
    assert "total_categories" in data
    assert "sales_summary" in data
    assert "low_stock_products" in data
    summary = data["sales_summary"]
    assert "total_revenue" in summary
    assert "completed_orders" in summary
    assert "pending_orders" in summary
    assert "cancelled_orders" in summary


def test_dashboard_requires_admin(client, customer_headers):
    resp = client.get("/admin/dashboard", headers=customer_headers)
    assert resp.status_code == 403


def test_dashboard_requires_auth(client):
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 401
