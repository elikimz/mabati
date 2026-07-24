"""Tests for authentication endpoints."""
import pytest
import httpx

BASE_URL = "http://localhost:8000"
_unique_email = "unique_auth_test@example.com"


def test_health(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Mabati" in data["app"]


def test_register_new_user(client):
    import time
    email = f"newuser_{int(time.time())}@example.com"
    resp = client.post("/auth/register", json={
        "name": "New User",
        "email": email,
        "password": "NewPass123!",
        "role": "customer",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email
    assert data["role"] == "customer"
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    email = "duplicate@example.com"
    payload = {"name": "Dup", "email": email, "password": "Pass1234!", "role": "customer"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_success(client, admin_token):
    assert len(admin_token) > 10


def test_login_wrong_password(client):
    resp = client.post("/auth/login", data={
        "username": "nobody@example.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


def test_get_me(client, admin_headers):
    resp = client.get("/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


def test_get_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_refresh_token(client, admin_token):
    # Get a refresh token first
    from tests.conftest import _admin_email, _test_password
    resp = client.post("/auth/login", data={
        "username": _admin_email,
        "password": _test_password,
    })
    refresh = resp.json()["refresh_token"]
    resp2 = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()


def test_refresh_invalid_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401
