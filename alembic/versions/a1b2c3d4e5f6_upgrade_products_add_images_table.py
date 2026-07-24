"""upgrade_products_add_images_table

Revision ID: a1b2c3d4e5f6
Revises: 7d8099527e1f
Create Date: 2026-07-24 14:00:00.000000

Adds new columns to products table (slug, product_type, material, finish, unit,
price_from, price_to, minimum_order_quantity, is_featured, is_available) and
creates the product_images table.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7d8099527e1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add new columns to products ──────────────────────────────────────────
    op.add_column("products", sa.Column("slug", sa.String(length=220), nullable=True))
    op.add_column("products", sa.Column("product_type", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("material", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("finish", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("unit", sa.String(length=20), nullable=True, server_default="piece"))
    op.add_column("products", sa.Column("price_from", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("products", sa.Column("price_to", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("products", sa.Column("minimum_order_quantity", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("products", sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("products", sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"))

    # Migrate existing price → price_from
    # Check if 'price' column exists before trying to migrate from it
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='products' AND column_name='price') THEN
                UPDATE products SET price_from = price WHERE price_from IS NULL;
            END IF;
        END $$;
        """
    )

    # Make price_from NOT NULL after migration
    op.alter_column("products", "price_from", type_=sa.Numeric(12, 2), nullable=False)

    # Create unique index on slug
    op.create_index(op.f("ix_products_slug"), "products", ["slug"], unique=True)
    op.create_index("ix_products_featured", "products", ["is_featured", "is_available"], unique=False)

    # ── Create product_images table ──────────────────────────────────────────
    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alt_text", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_images_id"), "product_images", ["id"], unique=False)
    op.create_index(op.f("ix_product_images_product_id"), "product_images", ["product_id"], unique=False)

    # Migrate existing image_url → product_images (primary image)
    op.execute(
        """
        INSERT INTO product_images (product_id, image_url, is_primary, display_order)
        SELECT id, image_url, true, 0
        FROM products
        WHERE image_url IS NOT NULL AND image_url != ''
        """
    )


def downgrade() -> None:
    op.drop_table("product_images")
    op.drop_index("ix_products_featured", table_name="products")
    op.drop_index(op.f("ix_products_slug"), table_name="products")
    op.drop_column("products", "is_available")
    op.drop_column("products", "is_featured")
    op.drop_column("products", "minimum_order_quantity")
    op.drop_column("products", "price_to")
    op.drop_column("products", "price_from")
    op.drop_column("products", "unit")
    op.drop_column("products", "finish")
    op.drop_column("products", "material")
    op.drop_column("products", "product_type")
    op.drop_column("products", "slug")
