"""
Pytest configuration and fixtures.

These tests run against the live Neon PostgreSQL database (same as production).
Each test cleans up after itself to avoid data pollution.
"""
import pytest
import httpx

BASE_URL = "http://localhost:8000"

# Shared state across tests
_admin_token: str = ""
_customer_token: str = ""
_admin_email = "testadmin@example.com"
_customer_email = "testcustomer@example.com"
_test_password = "TestPass123!"


@pytest.fixture(scope="session")
def client():
    """Synchronous HTTP client against the running server."""
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    """Register (or login) an admin user and return its access token."""
    # Try register first
    client.post("/auth/register", json={
        "name": "Test Admin",
        "email": _admin_email,
        "password": _test_password,
        "role": "admin",
    })
    resp = client.post("/auth/login", data={
        "username": _admin_email,
        "password": _test_password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def customer_token(client):
    """Register (or login) a customer user and return its access token."""
    client.post("/auth/register", json={
        "name": "Test Customer",
        "email": _customer_email,
        "password": _test_password,
        "role": "customer",
    })
    resp = client.post("/auth/login", data={
        "username": _customer_email,
        "password": _test_password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}
