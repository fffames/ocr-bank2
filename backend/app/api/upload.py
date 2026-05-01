from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
import aiofiles

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.services.ocr_service import get_ocr_service
from app.config import settings

router = APIRouter()


@router.post("/")
async def upload_images(
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    """
    Upload receipt images and process with OCR.

    Args:
        files: List of image files to upload
        db: Database session

    Returns:
        List of processed receipts with OCR results
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    # Ensure upload and image directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs(settings.image_storage_path, exist_ok=True)

    processed_receipts = []
    ocr_service = get_ocr_service()

    # Ensure upload and image directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs(settings.image_storage_path, exist_ok=True)

    processed_receipts = []
    ocr_service = get_ocr_service()

    for file in files:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Only images are allowed."
            )

        # Read file content
        content = await file.read()

        # Check file size
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is too large. Maximum size is {settings.max_upload_size} bytes"
            )

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        upload_path = os.path.join("uploads", unique_filename)
        final_path = os.path.join(settings.image_storage_path, unique_filename)

        try:
            # Save uploaded file temporarily
            async with aiofiles.open(upload_path, "wb") as f:
                await f.write(content)

            # Process with OCR
            ocr_result = ocr_service.extract_text_from_image(upload_path)

            # Move file to permanent storage
            os.rename(upload_path, final_path)

            # Create database record
            receipt = Receipt(
                filename=file.filename,
                image_path=final_path,
                ocr_raw_text=ocr_result["raw_text"],
                extracted_date=ocr_result["extracted_date"],
                extracted_time=ocr_result["extracted_time"],
                sender=ocr_result["sender"],
                receiver=ocr_result["receiver"],
                amount=ocr_result["amount"],
                note=ocr_result["note"],
                confidence_score=ocr_result["confidence_score"],
                status="pending"
            )

            db.add(receipt)
            db.commit()
            db.refresh(receipt)

            # Add to processed receipts
            receipt_data = {
                "id": receipt.id,
                "filename": receipt.filename,
                "image_path": receipt.image_path,
                "ocr_raw_text": receipt.ocr_raw_text,
                "extracted_date": receipt.extracted_date.isoformat() if receipt.extracted_date else None,
                "extracted_time": receipt.extracted_time.isoformat() if receipt.extracted_time else None,
                "sender": receipt.sender,
                "receiver": receipt.receiver,
                "amount": float(receipt.amount) if receipt.amount else None,
                "note": receipt.note,
                "confidence_score": float(receipt.confidence_score) if receipt.confidence_score else 0,
                "status": receipt.status,
                "created_at": receipt.created_at.isoformat(),
                "updated_at": receipt.updated_at.isoformat()
            }
            processed_receipts.append(receipt_data)

        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(upload_path):
                os.remove(upload_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file {file.filename}: {str(e)}"
            )

    return {
        "message": f"Successfully processed {len(processed_receipts)} receipt(s)",
        "receipts": processed_receipts
    }


@router.post("/process-ocr/{receipt_id}")
async def process_ocr_for_receipt(
    receipt_id: int,
    db: Session = Depends(get_db)
):
    """
    Re-process OCR for an existing receipt.

    Args:
        receipt_id: ID of the receipt to reprocess
        db: Database session

    Returns:
        Updated receipt with new OCR results
    """
    # Get receipt from database
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Check if image exists
    if not os.path.exists(receipt.image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    try:
        # Reprocess with OCR
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.extract_text_from_image(receipt.image_path)

        # Update receipt
        receipt.ocr_raw_text = ocr_result["raw_text"]
        receipt.extracted_date = ocr_result["extracted_date"]
        receipt.extracted_time = ocr_result["extracted_time"]
        receipt.sender = ocr_result["sender"]
        receipt.receiver = ocr_result["receiver"]
        receipt.amount = ocr_result["amount"]
        receipt.note = ocr_result["note"]
        receipt.confidence_score = ocr_result["confidence_score"]
        receipt.status = "pending"
        receipt.updated_at = datetime.now()

        db.commit()
        db.refresh(receipt)

        return {
            "id": receipt.id,
            "filename": receipt.filename,
            "image_path": receipt.image_path,
            "ocr_raw_text": receipt.ocr_raw_text,
            "extracted_date": receipt.extracted_date.isoformat() if receipt.extracted_date else None,
            "extracted_time": receipt.extracted_time.isoformat() if receipt.extracted_time else None,
            "sender": receipt.sender,
            "receiver": receipt.receiver,
            "amount": float(receipt.amount) if receipt.amount else None,
            "note": receipt.note,
            "confidence_score": float(receipt.confidence_score) if receipt.confidence_score else 0,
            "status": receipt.status,
            "created_at": receipt.created_at.isoformat(),
            "updated_at": receipt.updated_at.isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reprocessing OCR: {str(e)}"
        )
