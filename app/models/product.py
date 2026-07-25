"""SQLAlchemy ORM models for products, variations, and product images."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    """A sellable catalogue product that can expose one or more priced variations.

    The existing product-level specification, pricing, and inventory columns are
    intentionally retained. They continue to support legacy products and act as
    browse-friendly summary fields for products that have variations.
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Classification
    brand = Column(String(100), nullable=True)
    product_type = Column(String(100), nullable=True)  # e.g. "Roofing Sheet", "Gutter"
    material = Column(String(100), nullable=True)  # e.g. "Galvanized Steel", "Aluminium"
    finish = Column(String(100), nullable=True)  # e.g. "Matte", "Glossy", "Stone Coated"
    profile = Column(String(50), nullable=True)  # e.g. "Box Profile", "Versatile"

    # Legacy / summary physical specs. Variation-specific values belong on ProductVariation.
    gauge = Column(String(20), nullable=True, index=True)
    length = Column(Float, nullable=True)  # metres
    width = Column(Float, nullable=True)  # metres
    color = Column(String(50), nullable=True, index=True)
    unit = Column(String(20), nullable=True, default="piece")

    # Legacy / summary pricing. For variation-enabled products this is maintained
    # from the active variations, so catalogue clients can keep using these fields.
    price_from = Column(Numeric(12, 2), nullable=False)
    price_to = Column(Numeric(12, 2), nullable=True)
    discount_price = Column(Numeric(12, 2), nullable=True)

    # Product-level inventory remains the source of stock truth for compatibility.
    stock_quantity = Column(Integer, default=0, nullable=False)
    minimum_order_quantity = Column(Integer, default=1, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)

    # Status flags
    is_featured = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Legacy single image (kept for backward compatibility)
    image_url = Column(String(500), nullable=True)

    # Foreign key
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    category = relationship("Category", back_populates="products")
    variations = relationship(
        "ProductVariation",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariation.sort_order, ProductVariation.id",
        lazy="selectin",
    )
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.display_order",
        lazy="selectin",
    )
    inventory_logs = relationship("InventoryLog", back_populates="product", lazy="selectin")
    order_items = relationship("OrderItem", back_populates="product")

    # Composite indexes for common filter patterns
    __table_args__ = (
        Index("ix_products_category_active", "category_id", "is_active"),
        Index("ix_products_color_gauge", "color", "gauge"),
        Index("ix_products_featured", "is_featured", "is_available"),
    )


class ProductVariation(Base):
    """A specific purchasable configuration of a product with its own price.

    Common examples include a Roman Tile in 30 Gauge priced per metre and the
    same profile in 28 Gauge at a different price. The JSON specification map
    permits product-family-specific attributes without a schema change.
    """

    __tablename__ = "product_variations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Merchant-facing identifiers and display information
    name = Column(String(120), nullable=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    gauge = Column(String(20), nullable=True, index=True)
    size_label = Column(String(100), nullable=True)  # e.g. "3 m", "2.5 m × 0.9 m"
    length = Column(Float, nullable=True)  # metres
    width = Column(Float, nullable=True)  # metres
    color = Column(String(50), nullable=True, index=True)
    unit = Column(String(20), nullable=False, default="piece")

    # Pricing for this exact variation
    price = Column(Numeric(12, 2), nullable=False)
    discount_price = Column(Numeric(12, 2), nullable=True)

    # Flexible family-specific details, e.g. coating, ridge angle, diameter, pack size
    specifications = Column(JSON, nullable=False, default=dict)
    sort_order = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    product = relationship("Product", back_populates="variations")
    order_items = relationship("OrderItem", back_populates="variation")

    __table_args__ = (
        Index("ix_product_variations_product_active", "product_id", "is_active", "is_available"),
        Index("ix_product_variations_product_gauge", "product_id", "gauge"),
    )


class ProductImage(Base):
    """Multiple images per product with ordering and primary flag."""

    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    alt_text = Column(String(200), nullable=True)

    product = relationship("Product", back_populates="images")
