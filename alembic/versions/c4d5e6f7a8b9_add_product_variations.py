"""add_product_variations

Revision ID: c4d5e6f7a8b9
Revises: 3f9dec00eb25
Create Date: 2026-07-25 11:00:00.000000

Adds reusable, independently priced product variations. Existing products are
backfilled with a single variation so their current price and specification are
preserved. Existing order items remain valid and gain optional variation fields.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "3f9dec00eb25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_variations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("gauge", sa.String(length=20), nullable=True),
        sa.Column("size_label", sa.String(length=100), nullable=True),
        sa.Column("length", sa.Float(), nullable=True),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default="piece"),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("specifications", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_variations_id"), "product_variations", ["id"], unique=False)
    op.create_index(op.f("ix_product_variations_product_id"), "product_variations", ["product_id"], unique=False)
    op.create_index(op.f("ix_product_variations_sku"), "product_variations", ["sku"], unique=True)
    op.create_index(op.f("ix_product_variations_gauge"), "product_variations", ["gauge"], unique=False)
    op.create_index(op.f("ix_product_variations_color"), "product_variations", ["color"], unique=False)
    op.create_index(
        "ix_product_variations_product_active",
        "product_variations",
        ["product_id", "is_active", "is_available"],
        unique=False,
    )
    op.create_index(
        "ix_product_variations_product_gauge",
        "product_variations",
        ["product_id", "gauge"],
        unique=False,
    )

    # Make order variation selection and its display snapshot optional, so all
    # existing order rows remain valid and legacy order clients keep working.
    # SQLite cannot ALTER TABLE to add a foreign key, so it requires Alembic's
    # copy-and-move batch mode. PostgreSQL retains the direct, low-impact ALTER.
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("order_items") as batch_op:
            batch_op.add_column(sa.Column("variation_id", sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column("variation_snapshot", sa.JSON(), nullable=True))
            batch_op.create_index("ix_order_items_variation_id", ["variation_id"], unique=False)
            batch_op.create_foreign_key(
                "fk_order_items_variation_id_product_variations",
                "product_variations",
                ["variation_id"],
                ["id"],
                ondelete="SET NULL",
            )
    else:
        op.add_column("order_items", sa.Column("variation_id", sa.Integer(), nullable=True))
        op.add_column("order_items", sa.Column("variation_snapshot", sa.JSON(), nullable=True))
        op.create_index(op.f("ix_order_items_variation_id"), "order_items", ["variation_id"], unique=False)
        op.create_foreign_key(
            "fk_order_items_variation_id_product_variations",
            "order_items",
            "product_variations",
            ["variation_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Every existing product receives one equivalent variation. This is additive:
    # legacy product fields remain unchanged and old clients still see the values
    # they sent before this migration.
    op.execute(
        """
        INSERT INTO product_variations (
            product_id, name, gauge, length, width, color, unit, price,
            discount_price, specifications, sort_order, is_available, is_active,
            created_at, updated_at
        )
        SELECT
            p.id,
            CASE
                WHEN p.gauge IS NOT NULL AND p.gauge <> '' THEN 'Gauge ' || p.gauge
                ELSE NULL
            END,
            p.gauge,
            p.length,
            p.width,
            p.color,
            COALESCE(NULLIF(p.unit, ''), 'piece'),
            p.price_from,
            p.discount_price,
            '{}',
            0,
            p.is_available,
            p.is_active,
            p.created_at,
            p.updated_at
        FROM products p
        WHERE NOT EXISTS (
            SELECT 1
            FROM product_variations pv
            WHERE pv.product_id = p.id
        )
        """
    )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("order_items") as batch_op:
            batch_op.drop_constraint("fk_order_items_variation_id_product_variations", type_="foreignkey")
            batch_op.drop_index("ix_order_items_variation_id")
            batch_op.drop_column("variation_snapshot")
            batch_op.drop_column("variation_id")
    else:
        op.drop_constraint(
            "fk_order_items_variation_id_product_variations",
            "order_items",
            type_="foreignkey",
        )
        op.drop_index(op.f("ix_order_items_variation_id"), table_name="order_items")
        op.drop_column("order_items", "variation_snapshot")
        op.drop_column("order_items", "variation_id")

    op.drop_index("ix_product_variations_product_gauge", table_name="product_variations")
    op.drop_index("ix_product_variations_product_active", table_name="product_variations")
    op.drop_index(op.f("ix_product_variations_color"), table_name="product_variations")
    op.drop_index(op.f("ix_product_variations_gauge"), table_name="product_variations")
    op.drop_index(op.f("ix_product_variations_sku"), table_name="product_variations")
    op.drop_index(op.f("ix_product_variations_product_id"), table_name="product_variations")
    op.drop_index(op.f("ix_product_variations_id"), table_name="product_variations")
    op.drop_table("product_variations")
