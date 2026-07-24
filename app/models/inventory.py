"""Inventory log ORM model for stock tracking."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    change = Column(Integer, nullable=False)          # positive = restock, negative = sale/adjustment
    reason = Column(String(100), nullable=True)       # e.g. "restock", "sale", "adjustment"
    note = Column(Text, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="inventory_logs")
    user = relationship("User")
