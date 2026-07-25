"""Validate the variation product endpoints through a disposable local FastAPI app."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import AsyncSessionLocal, engine
from app.main import app
from app.core.dependencies import get_current_admin, get_db
from app.models.category import Category

DATABASE_PATH = Path("/tmp/mabati_variation_http_test.db")


async def reset_database() -> int:
    DATABASE_PATH.unlink(missing_ok=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        category = Category(name="HTTP Test Roofing")
        session.add(category)
        await session.commit()
        return category.id


async def local_db_override():
    async with AsyncSessionLocal() as session:
        yield session


async def local_admin_override():
    return {"id": 1, "role": "admin"}


def run() -> None:
    category_id = asyncio.run(reset_database())
    app.dependency_overrides[get_db] = local_db_override
    app.dependency_overrides[get_current_admin] = local_admin_override

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/admin/products",
                json={
                    "name": "Roman Tile Profile",
                    "category_id": category_id,
                    "stock_quantity": 25,
                    "variations": [
                        {
                            "name": "30 Gauge",
                            "sku": "HTTP-ROMAN-30",
                            "gauge": "30 Gauge",
                            "unit": "MTRS",
                            "price": "550.00",
                            "specifications": {"Profile": "Roman Tile", "Coating": "Colour coated"},
                        },
                        {
                            "name": "28 Gauge",
                            "sku": "HTTP-ROMAN-28",
                            "gauge": "28 Gauge",
                            "unit": "MTRS",
                            "price": "650.00",
                            "specifications": {"Profile": "Roman Tile", "Coating": "Colour coated"},
                        },
                    ],
                },
            )
            assert create_response.status_code == 201, create_response.text
            product = create_response.json()
            assert product["price_from"] == "550.00", product
            assert product["price_to"] == "650.00", product
            assert len(product["variations"]) == 2, product
            assert product["variations"][1]["effective_price"] == "650.00", product

            product_id = product["id"]
            filtered_response = client.get("/products", params={"gauge": "28 Gauge"})
            assert filtered_response.status_code == 200, filtered_response.text
            listing = filtered_response.json()
            assert len(listing) == 1 and listing[0]["id"] == product_id, listing
            assert listing[0]["variations"][1]["gauge"] == "28 Gauge", listing

            detail_response = client.get(f"/products/{product_id}")
            assert detail_response.status_code == 200, detail_response.text
            assert len(detail_response.json()["variations"]) == 2, detail_response.text

            update_response = client.put(
                f"/admin/products/{product_id}",
                json={
                    "variations": [
                        {**product["variations"][0], "price": "575.00"},
                        product["variations"][1],
                    ]
                },
            )
            assert update_response.status_code == 200, update_response.text
            updated = update_response.json()
            assert updated["price_from"] == "575.00", updated
            assert updated["price_to"] == "650.00", updated
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())

    print("HTTP flow verified: admin variation CRUD payload, public listing/detail, price range, and gauge filter.")


if __name__ == "__main__":
    run()
