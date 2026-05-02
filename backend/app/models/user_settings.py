"""User settings model for storing user preferences."""
from sqlalchemy import Column, Integer, String, Text
from app.database.base import Base


class UserSettings(Base):
    """User settings model."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255), nullable=True)  # User's actual name
    user_name_variations = Column(Text, nullable=True)  # JSON array of name variations (nicknames, etc.)
    preferred_language = Column(String(10), default="th")  # "th" or "en"
