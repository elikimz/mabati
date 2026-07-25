"""Verify the product-variation migration against the disposable legacy fixture."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_PATH = Path("/tmp/mabati_variations_test.db")
connection = sqlite3.connect(DATABASE_PATH)
connection.row_factory = sqlite3.Row

variation = connection.execute(
    """
    SELECT product_id, name, gauge, length, width, color, unit, price,
           discount_price, specifications, is_available, is_active
    FROM product_variations
    WHERE product_id = 1
    """
).fetchone()
assert variation is not None, "Existing product was not backfilled to a variation"
assert dict(variation) == {
    "product_id": 1,
    "name": "Gauge 30 Gauge",
    "gauge": "30 Gauge",
    "length": 3.0,
    "width": 1.0,
    "color": "Charcoal",
    "unit": "MTRS",
    "price": 550,
    "discount_price": None,
    "specifications": "{}",
    "is_available": 1,
    "is_active": 1,
}, dict(variation)

order_columns = {row[1] for row in connection.execute("PRAGMA table_info(order_items)")}
assert {"variation_id", "variation_snapshot"}.issubset(order_columns), order_columns
legacy_order = connection.execute(
    "SELECT id, product_id, quantity, unit_price, variation_id, variation_snapshot FROM order_items WHERE id = 1"
).fetchone()
assert tuple(legacy_order) == (1, 1, 12, 550, None, None), tuple(legacy_order)

foreign_keys = connection.execute("PRAGMA foreign_key_list(order_items)").fetchall()
assert any(row[2] == "product_variations" and row[3] == "variation_id" and row[6] == "SET NULL" for row in foreign_keys), foreign_keys
connection.close()
print("Migration backfill verified: legacy product, order item, variation fields, and FK are correct.")
