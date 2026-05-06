from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate, ReceiptResponse
from app.services.auth_service import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[ReceiptResponse])
def list_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sender: Optional[str] = None,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
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
        transaction_type: Filter by transaction type (sending, receiving, unknown)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of receipts for the current user
    """
    # Filter by current user
    query = db.query(Receipt).filter(Receipt.user_id == current_user.id)

    # Apply filters
    if status:
        query = query.filter(Receipt.status == status)

    if date_from:
        query = query.filter(Receipt.extracted_date >= date_from)

    if date_to:
        query = query.filter(Receipt.extracted_date <= date_to)

    if sender:
        query = query.filter(Receipt.sender.ilike(f"%{sender}%"))

    if transaction_type:
        query = query.filter(Receipt.transaction_type == transaction_type)

    # Order by most recent first
    query = query.order_by(Receipt.created_at.desc())

    # Apply pagination
    receipts = query.offset(skip).limit(limit).all()

    return receipts


@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific receipt by ID.

    Args:
        receipt_id: ID of the receipt
        current_user: Authenticated user
        db: Database session

    Returns:
        Receipt details
    """
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return receipt


@router.put("/{receipt_id}", response_model=ReceiptResponse)
def update_receipt(
    receipt_id: int,
    receipt_update: ReceiptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update receipt details (used in review page).

    Args:
        receipt_id: ID of the receipt to update
        receipt_update: Updated receipt data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated receipt
    """
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()

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
    # Add transaction_type support for editing
    if receipt_update.transaction_type is not None:
        receipt.transaction_type = receipt_update.transaction_type

    db.commit()
    db.refresh(receipt)

    return receipt


@router.post("/{receipt_id}/confirm", response_model=ReceiptResponse)
def confirm_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark receipt as confirmed (verified by user).

    Args:
        receipt_id: ID of the receipt to confirm
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated receipt with confirmed status
    """
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    receipt.status = "confirmed"
    db.commit()
    db.refresh(receipt)

    return receipt


@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a receipt.

    Args:
        receipt_id: ID of the receipt to delete
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Delete from vector store
    try:
        from app.services.vector_store import get_vector_store
        vector_store = get_vector_store()
        vector_store.delete_receipt(receipt_id)
        print(f"✅ Deleted receipt {receipt_id} from vector store")
    except Exception as e:
        print(f"⚠️  Could not delete from vector store: {e}")

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
def get_receipt_stats(
    year: int = None,
    month: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get overview statistics for receipts.

    Args:
        year: Filter by year (optional)
        month: Filter by month (optional)
        current_user: Authenticated user
        db: Database session

    Returns:
        Statistics including total receipts, total amount, and status counts
        Separated by transaction type (sending vs receiving)
        Includes income breakdown by category
    """
    from sqlalchemy import func
    from datetime import date

    # Build date filter if year/month provided
    date_filter = True
    if year and month:
        from calendar import monthrange
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
    else:
        start_date = None
        end_date = None
        date_filter = False

    # Base query with user filter and optional date filter
    def apply_filters(query):
        query = query.filter(Receipt.user_id == current_user.id)
        if date_filter:
            query = query.filter(
                Receipt.extracted_date >= start_date,
                Receipt.extracted_date <= end_date
            )
        return query

    # Total receipts
    total_receipts = apply_filters(db.query(Receipt)).count()

    # Calculate sending amount (paying out)
    sending_amount_result = apply_filters(db.query(func.sum(Receipt.amount))).filter(
        Receipt.transaction_type == "sending",
        Receipt.amount.isnot(None)
    ).first()
    sending_amount = float(sending_amount_result[0]) if sending_amount_result[0] else 0.0

    # Calculate receiving amount (income)
    receiving_amount_result = apply_filters(db.query(func.sum(Receipt.amount))).filter(
        Receipt.transaction_type == "receiving",
        Receipt.amount.isnot(None)
    ).first()
    receiving_amount = float(receiving_amount_result[0]) if receiving_amount_result[0] else 0.0

    # Net amount = receiving - sending
    net_amount = receiving_amount - sending_amount

    pending_count = apply_filters(db.query(Receipt)).filter(Receipt.status == "pending").count()
    reviewed_count = apply_filters(db.query(Receipt)).filter(Receipt.status == "reviewed").count()
    confirmed_count = apply_filters(db.query(Receipt)).filter(Receipt.status == "confirmed").count()

    # Count by transaction type
    sending_count = apply_filters(db.query(Receipt)).filter(Receipt.transaction_type == "sending").count()
    receiving_count = apply_filters(db.query(Receipt)).filter(Receipt.transaction_type == "receiving").count()

    # Income breakdown by category (including manual income and salary)
    income_by_category = []

    # Get all receiving transactions with income category
    receiving_with_category = apply_filters(db.query(Receipt)).filter(
        Receipt.transaction_type == "receiving",
        Receipt.income_category.isnot(None),
        Receipt.amount.isnot(None)
    ).all()

    # Group by income_category
    category_totals = {}
    for receipt in receiving_with_category:
        category = receipt.income_category or "Other Income"
        if category not in category_totals:
            category_totals[category] = {"total_amount": 0, "count": 0}
        category_totals[category]["total_amount"] += float(receipt.amount)
        category_totals[category]["count"] += 1

    # Convert to list format
    for category, data in category_totals.items():
        income_by_category.append({
            "category": category,
            "total_amount": data["total_amount"],
            "count": data["count"]
        })

    # Sort by total amount descending
    income_by_category.sort(key=lambda x: x["total_amount"], reverse=True)

    return {
        "total_receipts": total_receipts,
        "total_amount": net_amount,  # Changed to net amount
        "sending_amount": sending_amount,
        "receiving_amount": receiving_amount,
        "pending_count": pending_count,
        "reviewed_count": reviewed_count,
        "confirmed_count": confirmed_count,
        "sending_count": sending_count,
        "receiving_count": receiving_count,
        "income_by_category": income_by_category  # Now includes manual income!
    }


@router.post("/{receipt_id}/reprocess-ocr")
async def reprocess_receipt_ocr(
    receipt_id: int,
    template_id: str,
    ocr_method: str = "auto",  # Options: "auto", "template", "ai"
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Re-process a receipt with a specific template and OCR method.

    Args:
        receipt_id: ID of the receipt to reprocess
        template_id: Template ID to use for OCR
        ocr_method: OCR method to use ("auto", "template", "ai")
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated receipt with new OCR data
    """
    from app.services.template_ocr_service import get_template_ocr_service
    from app.services.gemini_vlm_service import get_gemini_vlm_service
    from app.config import settings

    # Get the receipt
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Use image_path as-is (it's already relative to project root: ./backend/images/...)
    image_path = receipt.image_path

    # Re-process OCR with specified template and method
    try:
        ocr_result = None
        final_ocr_engine = "template"

        # Method: AI Only (Gemini)
        if ocr_method == "ai":
            print(f"  🤖 Using AI Only (Gemini) method")
            vlm_service = get_gemini_vlm_service()
            ocr_result = vlm_service.extract_text_from_image(image_path)
            final_ocr_engine = "gemini"

        # Method: Template Only
        elif ocr_method == "template":
            print(f"  🎯 Using Template Only method")
            template_service = get_template_ocr_service()
            ocr_result = template_service.extract_from_image(image_path, template_id=template_id)
            final_ocr_engine = "template"

        # Method: Auto (Template + AI Fallback)
        else:  # ocr_method == "auto"
            print(f"  🔄 Using Auto (Template + AI Fallback) method")
            template_service = get_template_ocr_service()

            # Try template OCR first
            try:
                ocr_result = template_service.extract_from_image(image_path, template_id=template_id)
                print("  ✅ Template OCR successful")

                # Check if any key fields are None - use VLM as fallback
                key_fields = ['extracted_date', 'extracted_time', 'sender', 'receiver', 'amount']
                missing_fields = [field for field in key_fields if ocr_result.get(field) is None]

                if missing_fields and settings.vlm_fallback_enabled:
                    print(f"  ⚠️  Template OCR missing fields: {', '.join(missing_fields)}")
                    print("  🔄 Using Gemini Flash Lite as fallback for missing fields...")

                    try:
                        # Get VLM extraction for all fields
                        vlm_service = get_gemini_vlm_service()
                        vlm_result = vlm_service.extract_text_from_image(image_path)

                        # Fill in missing fields from VLM result
                        for field in missing_fields:
                            if vlm_result.get(field) is not None:
                                ocr_result[field] = vlm_result[field]
                                print(f"  ✅ VLM filled missing field: {field}")

                        # Update raw_text to include VLM data
                        if vlm_result.get("raw_text"):
                            ocr_result["raw_text"] += " | " + vlm_result["raw_text"]

                        # Update confidence score (lower for VLM fallback)
                        ocr_result["confidence_score"] = 0.75
                        final_ocr_engine = "template+vlm"

                        print(f"  ✅ VLM fallback successful - filled {len(missing_fields)} missing fields")
                    except Exception as vlm_error:
                        print(f"  ❌ VLM fallback failed: {vlm_error}")
                        # Continue with partial template OCR results
                elif missing_fields:
                    print(f"  ⚠️  Template OCR missing fields: {', '.join(missing_fields)}")
                    print("  ℹ️  VLM fallback is disabled (VLM_FALLBACK_ENABLED=false)")

            except Exception as template_error:
                print(f"  ⚠️  Template OCR failed: {template_error}")
                # Fallback to VLM
                try:
                    vlm_service = get_gemini_vlm_service()
                    ocr_result = vlm_service.extract_text_from_image(image_path)
                    final_ocr_engine = "gemini"
                    print("  ✅ VLM fallback successful")
                except Exception as vlm_error:
                    print(f"  ❌ VLM also failed: {vlm_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Both Template OCR and VLM failed: {str(vlm_error)}"
                    )

        # Update receipt with new OCR data
        if ocr_result.get("extracted_date"):
            receipt.extracted_date = ocr_result["extracted_date"]
        if ocr_result.get("extracted_time"):
            receipt.extracted_time = ocr_result["extracted_time"]
        if ocr_result.get("sender"):
            receipt.sender = ocr_result["sender"]
        if ocr_result.get("receiver"):
            receipt.receiver = ocr_result["receiver"]
        if ocr_result.get("amount") and str(ocr_result.get("amount")).strip():
            from decimal import Decimal
            receipt.amount = Decimal(str(ocr_result["amount"]))
        if ocr_result.get("note"):
            receipt.note = ocr_result["note"]
        if ocr_result.get("confidence_score"):
            from decimal import Decimal
            receipt.confidence_score = Decimal(str(ocr_result["confidence_score"]))

        # Update template and engine info
        receipt.detected_template = template_id
        receipt.ocr_engine = final_ocr_engine
        receipt.updated_at = datetime.now()

        db.commit()
        db.refresh(receipt)

        return receipt

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-process OCR: {str(e)}"
        )
