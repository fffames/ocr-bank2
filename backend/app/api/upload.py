from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import json
from datetime import datetime
import aiofiles

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.models.user_settings import UserSettings
from app.services.gemini_vlm_service import get_gemini_vlm_service
from app.services.vlm_service import get_vlm_service
from app.services.lm_studio_vlm_service import get_lm_studio_vlm_service
from app.services.template_ocr_service import get_template_ocr_service
from app.services.auth_service import get_current_active_user
from app.config import settings

router = APIRouter()


@router.post("/")
async def upload_images(
    files: Optional[List[UploadFile]] = File(None),
    template_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload receipt images and process with OCR.

    Args:
        files: List of image files to upload
        template_id: Optional template ID to force specific template
        current_user: Authenticated user
        db: Database session

    Returns:
        List of processed receipts with OCR results for the current user
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    # Ensure upload and image directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs(settings.image_storage_path, exist_ok=True)

    processed_receipts = []

    # Initialize services
    template_ocr_service = get_template_ocr_service()

    # Try Gemini VLM first (user's preferred choice)
    try:
        vlm_service = get_gemini_vlm_service()
        print("🌟 Gemini 1.5 Flash VLM available (primary fallback)")
    except Exception as e:
        print(f"⚠️  Gemini VLM not available: {e}")
        vlm_service = None

    # Fallback to Groq VLM if Gemini is not available
    if not vlm_service:
        try:
            vlm_service = get_vlm_service()
            print("☁️  Groq VLM available (secondary fallback)")
        except Exception as e:
            print(f"⚠️  Groq VLM not available: {e}")
            vlm_service = None

    # LM Studio as last resort
    if not vlm_service:
        try:
            vlm_service = get_lm_studio_vlm_service()
            print("🖥️  LM Studio VLM available (last resort)")
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

                # Check if any key fields are None - use VLM as fallback (if enabled)
                key_fields = ['extracted_date', 'extracted_time', 'sender', 'receiver', 'amount']
                missing_fields = [field for field in key_fields if ocr_result.get(field) is None]

                if missing_fields and vlm_service and settings.vlm_fallback_enabled:
                    print(f"  ⚠️  Template OCR missing fields: {', '.join(missing_fields)}")
                    print("  🔄 Using Gemini Flash Lite as fallback for missing fields...")

                    try:
                        # Get VLM extraction for all fields
                        vlm_result = vlm_service.extract_text_from_image(upload_path)

                        # Fill in missing fields from VLM result
                        for field in missing_fields:
                            if vlm_result.get(field) is not None:
                                ocr_result[field] = vlm_result[field]
                                print(f"  ✅ VLM filled missing field: {field}")

                        # Update raw_text to include VLM data
                        if vlm_result.get("raw_text"):
                            ocr_result["raw_text"] += " | " + vlm_result["raw_text"]

                        # Update confidence score (lower for VLM fallback)
                        ocr_result["confidence_score"] = 0.75  # Lower confidence when using VLM fallback
                        ocr_result["ocr_engine"] = "template+vlm"

                        print(f"  ✅ VLM fallback successful - filled {len(missing_fields)} missing fields")
                    except Exception as vlm_error:
                        print(f"  ❌ VLM fallback failed: {vlm_error}")
                        # Continue with partial template OCR results
                elif missing_fields:
                    print(f"  ⚠️  Template OCR missing fields: {', '.join(missing_fields)}")
                    print("  ℹ️  VLM fallback is disabled (VLM_FALLBACK_ENABLED=false)")
                    print("  💡 Enable VLM fallback in .env: VLM_FALLBACK_ENABLED=true")

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

            # Validate and clean OCR result before database insertion
            def clean_ocr_for_db(result: dict) -> dict:
                """Clean OCR result to prevent database errors."""
                cleaned = result.copy()

                # Convert empty strings to None for string fields
                for field in ['sender', 'receiver', 'note']:
                    if cleaned.get(field) == '' or cleaned.get(field) == 'None':
                        cleaned[field] = None

                # Handle amount: empty string or invalid → None
                amount = cleaned.get('amount')
                if amount == '' or amount == 'None' or amount is None:
                    cleaned['amount'] = None
                elif isinstance(amount, str):
                    # Try to parse amount, if fails set to None
                    try:
                        from decimal import Decimal
                        # Remove common currency symbols and commas
                        cleaned_amount = amount.replace(',', '').replace('฿', '').replace('บาท', '').strip()
                        if cleaned_amount:
                            cleaned['amount'] = Decimal(cleaned_amount)
                        else:
                            cleaned['amount'] = None
                    except:
                        print(f"  ⚠️  Invalid amount format: '{amount}', setting to None")
                        cleaned['amount'] = None

                return cleaned

            # Clean OCR result before database insertion
            ocr_result = clean_ocr_for_db(ocr_result)

            # Apply LLM-based text cleaning using user's name from settings
            try:
                from app.services.text_cleaning_service import get_text_cleaning_service
                from app.models.user_settings import UserSettings

                # Get user settings for text cleaning (for current user)
                user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

                if user_settings and user_settings.user_name:
                    # Parse name variations
                    try:
                        name_variations = json.loads(user_settings.user_name_variations) if user_settings.user_name_variations else []
                    except:
                        name_variations = []

                    # Clean OCR-extracted data
                    cleaner = get_text_cleaning_service()
                    extracted_data = {
                        "sender": ocr_result.get("sender", ""),
                        "receiver": ocr_result.get("receiver", ""),
                        "amount": str(ocr_result.get("amount", "")) if ocr_result.get("amount") is not None else None,
                        "note": ocr_result.get("note", ""),
                        "extracted_date": ocr_result.get("extracted_date", ""),
                        "extracted_time": ocr_result.get("extracted_time", "")
                    }

                    cleaned_data = cleaner.clean_extracted_data(
                        extracted_data=extracted_data,
                        user_name=user_settings.user_name,
                        name_variations=name_variations
                    )

                    # Use cleaned data for database record
                    ocr_result["sender"] = cleaned_data.get("sender") if cleaned_data.get("sender") else None
                    ocr_result["receiver"] = cleaned_data.get("receiver") if cleaned_data.get("receiver") else None
                    ocr_result["amount"] = cleaned_data.get("amount")  # Keep None if not present
                    ocr_result["note"] = cleaned_data.get("note") if cleaned_data.get("note") else None
                    if cleaned_data.get("extracted_date"):
                        ocr_result["extracted_date"] = cleaned_data["extracted_date"]
                    if cleaned_data.get("extracted_time"):
                        ocr_result["extracted_time"] = cleaned_data["extracted_time"]

                    print("  🧹 Applied LLM text cleaning")
                else:
                    print("  ⚠️  No user name set, skipping text cleaning")

            except Exception as cleaning_error:
                print(f"  ⚠️  Text cleaning failed, using original OCR data: {cleaning_error}")
                # Continue with original OCR data if cleaning fails

            # Create database record (associated with current user)
            receipt = Receipt(
                user_id=current_user.id,
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
                status="pending",
                detected_template=ocr_result.get("detected_template"),
                ocr_engine=ocr_result.get("ocr_engine", "template")
            )

            db.add(receipt)
            db.commit()
            db.refresh(receipt)

            # Classify transaction using extracted data from database
            try:
                from app.services.transaction_classifier import TransactionClassifier
                from app.models.user_settings import UserSettings

                # Get user settings (for current user)
                user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

                if (user_settings and user_settings.auto_classify and user_settings.user_name):
                    # Run classifier (reads sender/receiver from database)
                    classifier = TransactionClassifier()

                    # Parse name variations
                    try:
                        name_variations = json.loads(user_settings.user_name_variations) if user_settings.user_name_variations else []
                    except:
                        name_variations = []

                    classification = classifier.classify(
                        sender=receipt.sender,  # Read from database (already extracted)
                        receiver=receipt.receiver,  # Read from database (already extracted)
                        user_name=user_settings.user_name,
                        name_variations=name_variations
                    )

                    # Update receipt record with classification
                    receipt.transaction_type = classification["transaction_type"]
                    receipt.transaction_confidence = classification["confidence"]
                    receipt.classification_reason = classification["reason"]

                    db.commit()  # Save classification to database
                    db.refresh(receipt)

                    print(f"  ✅ Classified as: {classification['transaction_type']} ({classification['confidence']})")
                else:
                    print("  ⚠️  No user name set or auto-classify disabled, skipping classification")
                    receipt.transaction_type = "unknown"
                    receipt.transaction_confidence = "low"
                    db.commit()

            except Exception as classify_error:
                print(f"  ⚠️  Classification failed: {classify_error}")
                receipt.transaction_type = "unknown"
                receipt.transaction_confidence = "low"
                db.commit()

            # Auto-index in vector store for RAG chat
            try:
                from app.services.vector_store import get_vector_store
                vector_store = get_vector_store()

                # Only index if receipt has actual data
                if receipt.sender or receipt.receiver or receipt.amount:
                    receipt_data = {
                        'extracted_date': receipt.extracted_date.isoformat() if receipt.extracted_date else None,
                        'sender': receipt.sender,
                        'receiver': receipt.receiver,
                        'amount': float(receipt.amount) if receipt.amount else None,
                        'note': receipt.note,
                        'transaction_type': receipt.transaction_type  # Add transaction type
                    }
                    vector_store.index_receipt(receipt.id, receipt_data)
                    print(f"  ✅ Auto-indexed receipt {receipt.id} in vector store")
                else:
                    print(f"  ⚠️  Receipt {receipt.id} has no extracted data, skipping index")
            except Exception as index_error:
                print(f"  ⚠️  Failed to auto-index receipt: {index_error}")
                # Don't fail the upload if indexing fails

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
                "transaction_type": receipt.transaction_type,
                "transaction_confidence": receipt.transaction_confidence,
                "classification_reason": receipt.classification_reason,
                "detected_template": receipt.detected_template,
                "ocr_engine": receipt.ocr_engine,
                "is_salary": receipt.is_salary,
                "is_manual_income": receipt.is_manual_income,
                "income_category": receipt.income_category,
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

    # Initialize VLM service for fallback
    try:
        vlm_service = get_vlm_service()
        print("☁️  Groq VLM available (fallback)")
    except Exception as e:
        print(f"⚠️  Groq VLM not available: {e}")
        vlm_service = None

    try:
        # Try template-based OCR first if template is specified
        if hasattr(receipt, 'detected_template') and receipt.detected_template:
            try:
                from app.services.template_ocr_service import get_template_ocr_service
                template_ocr_service = get_template_ocr_service()
                print(f"  🎯 Reprocessing with template: {receipt.detected_template}")
                ocr_result = template_ocr_service.extract_from_image(receipt.image_path, template_id=receipt.detected_template)
                print("  ✅ Template OCR successful")

                # Check if any key fields are None - use VLM as fallback (if enabled)
                key_fields = ['extracted_date', 'extracted_time', 'sender', 'receiver', 'amount']
                missing_fields = [field for field in key_fields if ocr_result.get(field) is None]

                if missing_fields and settings.vlm_fallback_enabled:
                    print(f"  ⚠️  Template OCR missing fields: {', '.join(missing_fields)}")
                    print("  🔄 Using VLM fallback for missing fields...")

                    # Get VLM service
                    vlm_service = get_gemini_vlm_service()
                    vlm_result = vlm_service.extract_text_from_image(receipt.image_path)

                    # Fill in missing fields from VLM result
                    for field in missing_fields:
                        if vlm_result.get(field) is not None:
                            ocr_result[field] = vlm_result[field]
                            print(f"  ✅ VLM filled missing field: {field}")

                    # Update raw_text to include VLM data
                    if vlm_result.get("raw_text"):
                        ocr_result["raw_text"] += " | " + vlm_result["raw_text"]

                    # Update confidence score
                    ocr_result["confidence_score"] = 0.75
                    ocr_result["ocr_engine"] = "template+vlm"

                    print(f"  ✅ VLM fallback successful - filled {len(missing_fields)} missing fields")
                elif missing_fields:
                    print(f"  ⚠️  Template OCR missing fields: {', '.join(missing_fields)}")
                    print("  ℹ️  VLM fallback is disabled (VLM_FALLBACK_ENABLED=false)")
                    print("  💡 Enable VLM fallback in .env: VLM_FALLBACK_ENABLED=true")

            except Exception as template_error:
                print(f"  ⚠️  Template OCR failed: {template_error}")
                print("  🔄 Using VLM as fallback...")
                vlm_service = get_vlm_service()
                ocr_result = vlm_service.extract_text_from_image(receipt.image_path)
        else:
            # No template detected, use VLM directly
            vlm_service = get_vlm_service()
            ocr_result = vlm_service.extract_text_from_image(receipt.image_path)

        # Apply LLM-based text cleaning using user's name from settings
        try:
            from app.services.text_cleaning_service import get_text_cleaning_service

            # Get user settings for text cleaning
            user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

            if user_settings and user_settings.user_name:
                # Parse name variations
                try:
                    name_variations = json.loads(user_settings.user_name_variations) if user_settings.user_name_variations else []
                except:
                    name_variations = []

                # Clean OCR-extracted data
                cleaner = get_text_cleaning_service()
                extracted_data = {
                    "sender": ocr_result.get("sender", ""),
                    "receiver": ocr_result.get("receiver", ""),
                    "amount": str(ocr_result.get("amount", "")) if ocr_result.get("amount") else "",
                    "note": ocr_result.get("note", ""),
                    "extracted_date": ocr_result.get("extracted_date", ""),
                    "extracted_time": ocr_result.get("extracted_time", "")
                }

                cleaned_data = cleaner.clean_extracted_data(
                    extracted_data=extracted_data,
                    user_name=user_settings.user_name,
                    name_variations=name_variations
                )

                # Use cleaned data
                ocr_result["sender"] = cleaned_data.get("sender") if cleaned_data.get("sender") else None
                ocr_result["receiver"] = cleaned_data.get("receiver") if cleaned_data.get("receiver") else None
                ocr_result["amount"] = cleaned_data.get("amount")  # Keep None if not present
                ocr_result["note"] = cleaned_data.get("note") if cleaned_data.get("note") else None
                if cleaned_data.get("extracted_date"):
                    ocr_result["extracted_date"] = cleaned_data["extracted_date"]
                if cleaned_data.get("extracted_time"):
                    ocr_result["extracted_time"] = cleaned_data["extracted_time"]

                print("  🧹 Applied LLM text cleaning")
            else:
                print("  ⚠️  No user name set, skipping text cleaning")

        except Exception as cleaning_error:
            print(f"  ⚠️  Text cleaning failed, using original OCR data: {cleaning_error}")
            # Continue with original OCR data if cleaning fails

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

        # Auto-index in vector store for RAG chat
        try:
            from app.services.vector_store import get_vector_store
            vector_store = get_vector_store()

            # Only index if receipt has actual data
            if receipt.sender or receipt.receiver or receipt.amount:
                receipt_data = {
                    'extracted_date': receipt.extracted_date.isoformat() if receipt.extracted_date else None,
                    'sender': receipt.sender,
                    'receiver': receipt.receiver,
                    'amount': float(receipt.amount) if receipt.amount else None,
                    'note': receipt.note
                }
                vector_store.index_receipt(receipt.id, receipt_data)
                print(f"  ✅ Auto-indexed receipt {receipt.id} in vector store")
            else:
                print(f"  ⚠️  Receipt {receipt.id} has no extracted data, skipping index")
        except Exception as index_error:
            print(f"  ⚠️  Failed to auto-index receipt: {index_error}")
            # Don't fail the upload if indexing fails

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
