from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, Time, TIMESTAMP, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    image_path = Column(Text, nullable=False)
    ocr_raw_text = Column(Text)
    extracted_date = Column(Date)
    extracted_time = Column(Time)
    sender = Column(String(255))
    receiver = Column(String(255))
    amount = Column(DECIMAL(15, 2))
    note = Column(Text)
    confidence_score = Column(DECIMAL(5, 4))
    status = Column(String(50), default="pending")  # pending, reviewed, confirmed
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    context_receipts = Column(Integer)  # Will be JSON serialized
    created_at = Column(TIMESTAMP, server_default=func.now())
    llm_provider = Column(String(50), default="gemini")
