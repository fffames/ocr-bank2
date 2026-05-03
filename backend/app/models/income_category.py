from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.database.connection import Base


class IncomeCategory(Base):
    """User-defined income categories."""
    __tablename__ = "income_categories"

    id = Column(Integer, primary_key=True, index=True)
    """Primary key with index."""

    name = Column(String(100), nullable=False, unique=True)
    """Category name: 'Freelance', 'Bonus', 'Investment', etc."""

    color = Column(String(20), default="#10b981")
    """Hex color for UI display (default green)"""

    icon = Column(String(50), nullable=True)
    """Icon name for UI: 'briefcase', 'gift', 'trending-up', etc."""

    created_at = Column(TIMESTAMP, server_default=func.now())
    """Timestamp when category was created"""
