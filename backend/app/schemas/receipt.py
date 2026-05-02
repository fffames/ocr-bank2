from pydantic import BaseModel, Field
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional


class ReceiptBase(BaseModel):
    filename: str
    extracted_date: Optional[date] = None
    extracted_time: Optional[time] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    amount: Optional[Decimal] = None
    note: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    status: str = "pending"
    transaction_type: Optional[str] = None
    transaction_confidence: Optional[str] = None
    classification_reason: Optional[str] = None


class ReceiptCreate(ReceiptBase):
    image_path: str
    ocr_raw_text: Optional[str] = None


class ReceiptUpdate(BaseModel):
    extracted_date: Optional[date] = None
    extracted_time: Optional[time] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    amount: Optional[Decimal] = None
    note: Optional[str] = None
    status: Optional[str] = None
    transaction_type: Optional[str] = None


class ReceiptResponse(ReceiptBase):
    id: int
    image_path: str
    ocr_raw_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1, description="User query about receipts")
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    source_receipts: list[ReceiptResponse]
    session_id: str
