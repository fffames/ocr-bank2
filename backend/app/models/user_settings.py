"""User settings model for storing user preferences."""
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base


class UserSettings(Base):
    """User settings model."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)  # NEW: User ownership (one-to-one)
    user_name = Column(String(255), nullable=True)  # User's actual name
    user_name_variations = Column(Text, nullable=True)  # JSON array of name variations (nicknames, etc.)
    auto_classify = Column(Boolean, default=True, nullable=False)  # Enable/disable auto-classification

    # Salary configuration
    default_salary_amount = Column(Numeric(10, 2), nullable=True)  # Monthly salary amount
    salary_day_of_month = Column(Integer, default=1, nullable=False)  # Day of month for salary
    salary_category = Column(String(100), default="Salary", nullable=False)  # Category name for salary

    # Relationship to user
    user = relationship("User", backref="settings")
