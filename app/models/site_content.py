"""SQLAlchemy model for generic site content and settings."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from app.database.base import Base

class SiteContent(Base):
    __tablename__ = "site_content"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)  # Store structured data like lists of stats or testimonials
    description = Column(String(200), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
