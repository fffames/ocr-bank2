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
from app.services.vlm_service import get_vlm_service
from app.services.lm_studio_vlm_service import get_lm_studio_vlm_service
from app.services.template_ocr_service import get_template_ocr_service
from app.config import settings

router = APIRouter()


@router.post("/")
async def upload_images(
    files: Optional[List[UploadFile]] = File(None),
    template_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload receipt images and process with OCR.

    Args:
        files: List of image files to upload
        template_id: Optional template ID to force specific template
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

    # Initialize services
    template_ocr_service = get_template_ocr_service()

    # Prefer Groq VLM as fallback (more reliable than LM Studio)
    try:
        vlm_service = get_vlm_service()
        print("☁️  Groq VLM available (fallback)")
    except Exception as e:
        print(f"⚠️  Groq VLM not available: {e}")
        vlm_service = None

    # LM Studio as secondary fallback
    if not vlm_service:
        try:
            vlm_service = get_lm_studio_vlm_service()
            print("🖥️  LM Studio VLM available (secondary fallback)")
        except Exception as e:
            print(f"⚠️  LM Studio VLM not available: {e}")
            vlm_service = None

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

            # Process with Template OCR (primary) or VLM (fallback)
            print(f"Processing {file.filename}...")
            ocr_result = None

            try:
                # Try template-based OCR first
                if template_id:
                    print(f"  🎯 Using specified template: {template_id}")
                    ocr_result = template_ocr_service.extract_from_image(upload_path, template_id=template_id)
                    print("  ✅ Template OCR successful")
                else:
                    print("  🎯 Attempting template auto-detection...")
                    ocr_result = template_ocr_service.extract_from_image(upload_path)
                    print("  ✅ Template OCR successful")
            except Exception as template_error:
                print(f"  ⚠️  Template OCR failed: {template_error}")
                if vlm_service:
                    print("  🔄 Falling back to VLM...")
                    try:
                        ocr_result = vlm_service.extract_text_from_image(upload_path)
                        print("  ✅ VLM fallback successful")
                    except Exception as vlm_error:
                        print(f"  ❌ VLM also failed: {vlm_error}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Both Template OCR and VLM failed: {str(vlm_error)}"
                        )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Template OCR failed and no VLM fallback available: {str(template_error)}"
                    )

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
        # Reprocess with VLM
        vlm_service = get_vlm_service()
        ocr_result = vlm_service.extract_text_from_image(receipt.image_path)

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
