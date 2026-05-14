from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, Time, TIMESTAMP, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # NEW: User ownership
    filename = Column(String(255), nullable=False)
    image_path = Column(Text, nullable=True)  # Nullable: image deleted after confirmation
    ocr_raw_text = Column(Text)
    extracted_date = Column(Date)
    extracted_time = Column(Time)
    sender = Column(String(255))
    receiver = Column(String(255))
    amount = Column(DECIMAL(15, 2))
    note = Column(Text)
    confidence_score = Column(DECIMAL(5, 4))
    status = Column(String(50), default="pending")  # pending, reviewed, confirmed
    transaction_type = Column(String(20), nullable=True)  # "sending", "receiving", "unknown"
    transaction_confidence = Column(String(10), nullable=True)  # "high", "medium", "low"
    classification_reason = Column(Text, nullable=True)  # Why classified this way
    is_salary = Column(Boolean, default=False, nullable=False)  # Is this a salary entry?
    is_manual_income = Column(Boolean, default=False, nullable=False)  # Is this manually added income?
    income_category = Column(String(100), nullable=True)  # Category for income (Salary, Freelance, etc.)
    detected_template = Column(String(100), nullable=True)  # Template ID used for OCR extraction
    ocr_engine = Column(String(50), default="template")  # OCR engine used: 'template' or 'vlm'
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship to user
    user = relationship("User", backref="receipts")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # NEW: User ownership (nullable for backward compatibility)
    session_id = Column(String(255), nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    context_receipts = Column(Text)  # JSON serialized list of receipt IDs
    created_at = Column(TIMESTAMP, server_default=func.now())
    llm_provider = Column(String(50), default="gemini")

    # Relationship to user
    user = relationship("User", backref="chat_history")
