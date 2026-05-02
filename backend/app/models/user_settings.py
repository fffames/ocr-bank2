"""User settings model for storing user preferences."""
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database.connection import Base


class UserSettings(Base):
    """User settings model."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255), nullable=True)  # User's actual name
    user_name_variations = Column(Text, nullable=True)  # JSON array of name variations (nicknames, etc.)
    auto_classify = Column(Boolean, default=True, nullable=False)  # Enable/disable auto-classification
