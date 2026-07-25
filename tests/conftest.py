"""Safe, isolated pytest fixtures for the Mabati API.

The test process forces a disposable SQLite database before importing the app,
so no regression test can access the configured remote PostgreSQL database.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DATABASE_PATH = Path("/tmp/mabati_pytest.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DATABASE_PATH}"
os.environ["DEBUG"] = "false"

from app.database.base import Base
from app.database.session import engine
from app.main import app

_admin_email = "testadmin@example.com"
_customer_email = "testcustomer@example.com"
_test_password = "TestPass123!"


async def _reset_database() -> None:
    DATABASE_PATH.unlink(missing_ok=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def isolated_database():
    """Create and remove the disposable schema used by the complete test suite."""
    asyncio.run(_reset_database())
    yield
    asyncio.run(engine.dispose())
    DATABASE_PATH.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def client(isolated_database):
    """Synchronous in-process HTTP client backed by the disposable database."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_token(client):
    """Register an isolated admin and return its bearer token."""
    email = _admin_email
    registration = client.post(
        "/auth/register",
        json={"name": "Test Admin", "email": email, "password": _test_password, "role": "admin"},
    )
    assert registration.status_code == 201, registration.text
    response = client.post("/auth/login", data={"username": email, "password": _test_password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def customer_token(client):
    """Register an isolated customer and return its bearer token."""
    email = _customer_email
    registration = client.post(
        "/auth/register",
        json={"name": "Test Customer", "email": email, "password": _test_password, "role": "customer"},
    )
    assert registration.status_code == 201, registration.text
    response = client.post("/auth/login", data={"username": email, "password": _test_password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}
