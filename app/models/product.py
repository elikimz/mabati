"""SQLAlchemy ORM model for Product and ProductImage."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Classification
    brand = Column(String(100), nullable=True)
    product_type = Column(String(100), nullable=True)   # e.g. "Roofing Sheet", "Gutter"
    material = Column(String(100), nullable=True)       # e.g. "Galvanized Steel", "Aluminium"
    finish = Column(String(100), nullable=True)         # e.g. "Matte", "Glossy", "Stone Coated"
    profile = Column(String(50), nullable=True)         # e.g. "Box Profile", "Versatile"

    # Physical specs
    gauge = Column(String(20), nullable=True, index=True)   # e.g. "28G", "30G"
    length = Column(Float, nullable=True)                   # metres
    width = Column(Float, nullable=True)                    # metres
    color = Column(String(50), nullable=True, index=True)
    unit = Column(String(20), nullable=True, default="piece")  # piece, metre, bundle

    # Pricing — range-based (price_from is the minimum / starting price)
    price_from = Column(Numeric(12, 2), nullable=False)
    price_to = Column(Numeric(12, 2), nullable=True)    # NULL means single price
    discount_price = Column(Numeric(12, 2), nullable=True)

    # Inventory
    stock_quantity = Column(Integer, default=0, nullable=False)
    minimum_order_quantity = Column(Integer, default=1, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)

    # Status flags
    is_featured = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Legacy single image (kept for backward compat)
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
