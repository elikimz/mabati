"""Product ORM model for Mabati roofing materials."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, Numeric, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    discount_price = Column(Numeric(12, 2), nullable=True)

    # Roofing-specific attributes
    color = Column(String(50), nullable=True, index=True)
    gauge = Column(String(20), nullable=True, index=True)   # e.g. "0.3mm", "0.4mm"
    length = Column(Float, nullable=True)                   # metres
    width = Column(Float, nullable=True)                    # metres
    profile = Column(String(50), nullable=True)             # e.g. "Box Profile", "Corrugated"

    # Inventory
    stock_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)

    # Media & status
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

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
    inventory_logs = relationship("InventoryLog", back_populates="product", lazy="selectin")
    order_items = relationship("OrderItem", back_populates="product")

    # Composite indexes for common filter patterns
    __table_args__ = (
        Index("ix_products_category_active", "category_id", "is_active"),
        Index("ix_products_color_gauge", "color", "gauge"),
    )
