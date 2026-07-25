"""Create a disposable pre-variation SQLite database for migration verification."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_PATH = Path("/tmp/mabati_variations_test.db")
DATABASE_PATH.unlink(missing_ok=True)

connection = sqlite3.connect(DATABASE_PATH)
connection.execute("PRAGMA foreign_keys = ON")
connection.executescript(
    """
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        gauge VARCHAR(20),
        length FLOAT,
        width FLOAT,
        color VARCHAR(50),
        unit VARCHAR(20),
        price_from NUMERIC(12, 2) NOT NULL,
        price_to NUMERIC(12, 2),
        discount_price NUMERIC(12, 2),
        is_available BOOLEAN NOT NULL DEFAULT 1,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at DATETIME,
        updated_at DATETIME
    );

    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price NUMERIC(12, 2) NOT NULL
    );

    INSERT INTO products (
        id, name, gauge, length, width, color, unit, price_from,
        discount_price, is_available, is_active, created_at, updated_at
    ) VALUES (
        1, 'Roman Tile Profile', '30 Gauge', 3.0, 1.0, 'Charcoal', 'MTRS',
        550.00, NULL, 1, 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00'
    );

    INSERT INTO order_items (id, product_id, quantity, unit_price)
    VALUES (1, 1, 12, 550.00);
    """
)
connection.commit()
connection.close()
print(DATABASE_PATH)
