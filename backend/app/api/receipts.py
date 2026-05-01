from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate, ReceiptResponse

router = APIRouter()


@router.get("/", response_model=List[ReceiptResponse])
def list_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sender: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List receipts with optional filters and pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (pending, reviewed, confirmed)
        date_from: Filter by date from (inclusive)
        date_to: Filter by date to (inclusive)
        sender: Filter by sender name
        db: Database session

    Returns:
        List of receipts
    """
    query = db.query(Receipt)

    # Apply filters
    if status:
        query = query.filter(Receipt.status == status)

    if date_from:
        query = query.filter(Receipt.extracted_date >= date_from)

    if date_to:
        query = query.filter(Receipt.extracted_date <= date_to)

    if sender:
        query = query.filter(Receipt.sender.ilike(f"%{sender}%"))

    # Order by most recent first
    query = query.order_by(Receipt.created_at.desc())

    # Apply pagination
    receipts = query.offset(skip).limit(limit).all()

    return receipts


@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """
    Get a specific receipt by ID.

    Args:
        receipt_id: ID of the receipt
        db: Database session

    Returns:
        Receipt details
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return receipt


@router.put("/{receipt_id}", response_model=ReceiptResponse)
def update_receipt(
    receipt_id: int,
    receipt_update: ReceiptUpdate,
    db: Session = Depends(get_db)
):
    """
    Update receipt details (used in review page).

    Args:
        receipt_id: ID of the receipt to update
        receipt_update: Updated receipt data
        db: Database session

    Returns:
        Updated receipt
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Update fields if provided
    if receipt_update.extracted_date is not None:
        receipt.extracted_date = receipt_update.extracted_date
    if receipt_update.extracted_time is not None:
        receipt.extracted_time = receipt_update.extracted_time
    if receipt_update.sender is not None:
        receipt.sender = receipt_update.sender
    if receipt_update.receiver is not None:
        receipt.receiver = receipt_update.receiver
    if receipt_update.amount is not None:
        receipt.amount = receipt_update.amount
    if receipt_update.note is not None:
        receipt.note = receipt_update.note
    if receipt_update.status is not None:
        receipt.status = receipt_update.status

    db.commit()
    db.refresh(receipt)

    return receipt


@router.post("/{receipt_id}/confirm", response_model=ReceiptResponse)
def confirm_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """
    Mark receipt as confirmed (verified by user).

    Args:
        receipt_id: ID of the receipt to confirm
        db: Database session

    Returns:
        Updated receipt with confirmed status
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    receipt.status = "confirmed"
    db.commit()
    db.refresh(receipt)

    return receipt


@router.delete("/{receipt_id}")
def delete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """
    Delete a receipt.

    Args:
        receipt_id: ID of the receipt to delete
        db: Database session

    Returns:
        Success message
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Delete image file
    import os
    try:
        if os.path.exists(receipt.image_path):
            os.remove(receipt.image_path)
    except Exception as e:
        print(f"Warning: Could not delete image file: {e}")

    # Delete database record
    db.delete(receipt)
    db.commit()

    return {"message": "Receipt deleted successfully"}


@router.get("/stats/overview")
def get_receipt_stats(db: Session = Depends(get_db)):
    """
    Get overview statistics for receipts.

    Args:
        db: Database session

    Returns:
        Statistics including total receipts, total amount, and status counts
    """
    total_receipts = db.query(Receipt).count()

    from sqlalchemy import func
    total_amount_result = db.query(func.sum(Receipt.amount)).filter(Receipt.amount.isnot(None)).first()
    total_amount = float(total_amount_result[0]) if total_amount_result[0] else 0.0

    pending_count = db.query(Receipt).filter(Receipt.status == "pending").count()
    reviewed_count = db.query(Receipt).filter(Receipt.status == "reviewed").count()
    confirmed_count = db.query(Receipt).filter(Receipt.status == "confirmed").count()

    return {
        "total_receipts": total_receipts,
        "total_amount": total_amount,
        "pending_count": pending_count,
        "reviewed_count": reviewed_count,
        "confirmed_count": confirmed_count
    }
