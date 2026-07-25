"""cleanup_products_drop_legacy_price_column

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-25

Drops the legacy ``price`` column from the ``products`` table that was left
behind after the ``a1b2c3d4e5f6`` migration added ``price_from`` and
``price_to``.  The application models have never referenced this column —
it is dead weight that causes confusion and potential INSERT errors when
databases are created via different code paths.

For production databases that went through the full Alembic chain, the
``price`` column still exists because ``a1b2c3d4e5f6`` never dropped it.
For databases created via ``Base.metadata.create_all()``, the column was
never created.  This migration normalises both paths.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the legacy price column from products.

    We only attempt the drop if the column actually exists, so the migration
    is safe to run against databases created via ``Base.metadata.create_all()``
    (where the column was never present).
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)
    product_columns = [col["name"] for col in insp.get_columns("products")]

    if "price" in product_columns:
        op.drop_column("products", "price")

    # Safety check: ensure all existing products have price_from set.
    # Products with price_from = 0 are legacy products that had no price at all.
    # Set price_from to 0 explicitly for consistency (NOT NULL).
    bind.execute(
        sa.text(
            "UPDATE products SET price_from = 0 WHERE price_from IS NULL"
        )
    )
    bind.commit()


def downgrade() -> None:
    """Restore the legacy price column (nullable, nullable default).

    This is a no-op reversal — we cannot reconstruct the original values,
    but we recreate the column so that ``alembic downgrade`` works cleanly.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)
    product_columns = [col["name"] for col in insp.get_columns("products")]

    if "price" not in product_columns:
        op.add_column(
            "products",
            sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=True),
        )
        # Backfill from price_from for convenience.
        bind.execute(
            sa.text(
                "UPDATE products SET price = price_from WHERE price IS NULL AND price_from IS NOT NULL"
            )
        )
        bind.commit()
