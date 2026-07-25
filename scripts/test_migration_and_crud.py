"""Comprehensive test: simulate production DB with full migration chain,
then verify product CRUD operations work correctly with the new pricing schema.

This script:
1. Creates a fresh SQLite database
2. Runs the FULL Alembic migration chain (simulating alembic upgrade head)
3. Verifies the legacy 'price' column is removed
4. Tests product creation, reading, updating, and deletion
5. Verifies the pricing architecture is consistent
"""
import asyncio
import os
import sys

# Set up environment before importing app modules
DB_PATH = "/tmp/mabati_full_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"
os.environ["SECRET_KEY"] = "test-secret-key-for-full-migration-test-1234567890abcdef"


def test_migration_chain():
    """Test that the full Alembic migration chain produces the correct schema."""
    print("=" * 70)
    print("TEST 1: Full Alembic Migration Chain")
    print("=" * 70)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # Run all migrations using alembic CLI
    print("Running: alembic upgrade head ...")
    result = os.system(
        f'cd /home/ubuntu/mabati && DATABASE_URL="{os.environ["DATABASE_URL"]}" '
        f'SECRET_KEY="{os.environ["SECRET_KEY"]}" '
        f'python3 -m alembic upgrade head 2>&1'
    )
    assert result == 0, "Alembic upgrade head failed"

    # Verify schema using synchronous SQLite
    from sqlalchemy import create_engine, inspect

    engine = create_engine(f"sqlite:///{DB_PATH}")
    insp = inspect(engine)
    tables = insp.get_table_names()
    print(f"  Tables: {tables}")

    # Check products table columns
    product_columns = [col["name"] for col in insp.get_columns("products")]
    print(f"  Products columns: {product_columns}")

    has_price = "price" in product_columns
    has_price_from = "price_from" in product_columns
    has_price_to = "price_to" in product_columns

    assert not has_price, "FAIL: Legacy 'price' column still exists in products table!"
    assert has_price_from, "FAIL: 'price_from' column missing from products table!"
    assert has_price_to, "FAIL: 'price_to' column missing from products table!"

    print("  PASS: No legacy 'price' column")
    print("  PASS: 'price_from' column exists")
    print("  PASS: 'price_to' column exists")

    # Check product_variations table
    variation_columns = [col["name"] for col in insp.get_columns("product_variations")]
    print(f"  ProductVariation columns: {variation_columns}")
    assert "price" in variation_columns, "FAIL: 'price' column missing from product_variations!"
    print("  PASS: Variation 'price' column exists (correct — variations have their own price)")

    engine.dispose()
    print("\n  All migration schema checks PASSED!\n")


def test_product_crud():
    """Test product CRUD operations through the API."""
    print("=" * 70)
    print("TEST 2: Product CRUD via FastAPI TestClient")
    print("=" * 70)

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Register admin user
    print("  Registering admin user...")
    response = client.post("/auth/register", json={
        "name": "Test Admin",
        "email": "admin@test.com",
        "password": "TestPassword123!",
        "role": "admin",
    })
    assert response.status_code == 201, f"Admin registration failed: {response.text}"
    print(f"  Admin registered: {response.json()['name']}")

    # Login
    print("  Logging in...")
    response = client.post("/auth/login", data={
        "username": "admin@test.com",
        "password": "TestPassword123!",
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("  Logged in successfully")

    # Create category
    print("  Creating category...")
    response = client.post("/admin/categories", json={"name": "Roofing Sheets"}, headers=admin_headers)
    assert response.status_code == 201, f"Category creation failed: {response.text}"
    category_id = response.json()["id"]
    print(f"  Category created: {response.json()['name']} (id={category_id})")

    # Create product with variations (range pricing)
    print("\n  Creating product with variations (Roman Tile)...")
    response = client.post("/admin/products", json={
        "name": "Roman Tile Profile",
        "description": "Premium Roman tile profile roofing sheet",
        "brand": "Mabati Rolling Mills",
        "product_type": "Roofing Sheet",
        "material": "Galvanized Steel",
        "profile": "Roman Tile",
        "category_id": category_id,
        "stock_quantity": 1000,
        "minimum_order_quantity": 1,
        "low_stock_threshold": 10,
        "is_active": True,
        "is_available": True,
        "variations": [
            {"name": "Gauge 30", "gauge": "30", "unit": "MTRS", "price": 550.00},
            {"name": "Gauge 28", "gauge": "28", "unit": "MTRS", "price": 650.00},
            {"name": "Gauge 26", "gauge": "26", "unit": "MTRS", "price": 750.00},
        ],
    }, headers=admin_headers)
    assert response.status_code == 201, f"Product creation failed: {response.text}"
    product = response.json()
    product_id = product["id"]
    print(f"  Product created: {product['name']} (id={product_id})")
    print(f"    price_from: {product.get('price_from')}")
    print(f"    price_to: {product.get('price_to')}")
    print(f"    variations: {len(product.get('variations', []))}")

    # Verify price range was calculated
    assert float(product["price_from"]) == 550.0, f"Expected price_from=550, got {product['price_from']}"
    assert float(product["price_to"]) == 750.0, f"Expected price_to=750, got {product['price_to']}"
    assert len(product["variations"]) == 3
    print("  PASS: Price range calculated correctly (550 - 750)")

    # Verify no 'price' field in response
    assert "price" not in product, "FAIL: 'price' field should not be in product response!"
    print("  PASS: No legacy 'price' field in response")

    # Get product detail
    print("\n  Getting product detail...")
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200, f"Product detail failed: {response.text}"
    detail = response.json()
    assert float(detail["price_from"]) == 550.0
    assert float(detail["price_to"]) == 750.0
    print(f"  PASS: Product detail returns correct pricing (from={detail['price_from']}, to={detail['price_to']})")

    # List products
    print("\n  Listing products...")
    response = client.get("/products")
    assert response.status_code == 200, f"Product listing failed: {response.text}"
    products_list = response.json()
    assert len(products_list) >= 1
    assert "price" not in products_list[0], "FAIL: Listing should not have legacy 'price' field!"
    print(f"  PASS: Product listing works ({len(products_list)} products)")

    # Create product with legacy single price (no variations)
    print("\n  Creating legacy single-price product...")
    response = client.post("/admin/products", json={
        "name": "Nails 50mm",
        "description": "Standard roofing nails",
        "category_id": category_id,
        "price_from": 150.00,
        "stock_quantity": 500,
        "is_active": True,
        "is_available": True,
    }, headers=admin_headers)
    assert response.status_code == 201, f"Legacy product creation failed: {response.text}"
    legacy_product = response.json()
    assert float(legacy_product["price_from"]) == 150.0
    assert legacy_product.get("price_to") is None
    assert len(legacy_product.get("variations", [])) == 0
    print(f"  PASS: Legacy single-price product created (price_from={legacy_product['price_from']})")

    # Update product (add a variation)
    print("\n  Updating product (adding variation)...")
    response = client.put(f"/admin/products/{product_id}", json={
        "name": "Roman Tile Profile - Updated",
        "description": "Premium Roman tile profile roofing sheet - Updated",
        "category_id": category_id,
        "stock_quantity": 900,
        "is_active": True,
        "is_available": True,
        "variations": [
            {"id": product["variations"][0]["id"], "name": "Gauge 30", "gauge": "30", "unit": "MTRS", "price": 560.00},
            {"id": product["variations"][1]["id"], "name": "Gauge 28", "gauge": "28", "unit": "MTRS", "price": 660.00},
            {"id": product["variations"][2]["id"], "name": "Gauge 26", "gauge": "26", "unit": "MTRS", "price": 760.00},
            {"name": "Gauge 24", "gauge": "24", "unit": "MTRS", "price": 860.00},
        ],
    }, headers=admin_headers)
    assert response.status_code == 200, f"Product update failed: {response.text}"
    updated = response.json()
    assert float(updated["price_from"]) == 560.0, f"Expected price_from=560, got {updated['price_from']}"
    assert float(updated["price_to"]) == 860.0, f"Expected price_to=860, got {updated['price_to']}"
    assert len(updated["variations"]) == 4
    print(f"  PASS: Product updated with new variation (price_from={updated['price_from']}, price_to={updated['price_to']})")

    # Delete legacy product
    print("\n  Deleting legacy product...")
    response = client.delete(f"/admin/products/{legacy_product['id']}", headers=admin_headers)
    assert response.status_code == 204, f"Product deletion failed: {response.text}"
    print("  PASS: Legacy product deleted")

    # Verify deleted product is gone
    response = client.get(f"/products/{legacy_product['id']}")
    assert response.status_code == 404
    print("  PASS: Deleted product returns 404")

    print("\n  All CRUD tests PASSED!\n")


def test_dashboard():
    """Test that the dashboard works with the new pricing schema."""
    print("=" * 70)
    print("TEST 3: Dashboard Integration")
    print("=" * 70)

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Login as admin
    response = client.post("/auth/login", data={
        "username": "admin@test.com",
        "password": "TestPassword123!",
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get dashboard data
    response = client.get("/admin/dashboard", headers=headers)
    assert response.status_code == 200, f"Dashboard failed: {response.text}"
    dashboard = response.json()
    print(f"  Dashboard data: {list(dashboard.keys())}")
    print(f"  Total products: {dashboard.get('total_products')}")
    print(f"  Total revenue: {dashboard.get('total_revenue')}")
    print("  PASS: Dashboard works correctly\n")


def main():
    print("\n" + "=" * 70)
    print("COMPREHENSIVE PRODUCT PRICING SCHEMA TEST")
    print("=" * 70 + "\n")

    try:
        test_migration_chain()
    except Exception as e:
        print(f"\n  MIGRATION TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

    try:
        test_product_crud()
    except Exception as e:
        print(f"\n  CRUD TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

    try:
        test_dashboard()
    except Exception as e:
        print(f"\n  DASHBOARD TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
