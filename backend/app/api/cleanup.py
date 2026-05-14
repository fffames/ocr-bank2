"""
Cleanup utility for old receipt images.

Removes images that are older than a specified number of days
for receipts in pending/reviewed status to save storage space.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.services.auth_service import get_current_active_user
from app.config import settings

router = APIRouter()


@router.post("/images/old")
def cleanup_old_images(
    days_old: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete images for receipts older than specified days that are not confirmed.

    Args:
        days_old: Delete images older than this many days (default: 7)
        current_user: Authenticated user
        db: Database session

    Returns:
        Summary of cleanup results
    """
    cutoff_date = datetime.now() - timedelta(days=days_old)

    # Find old receipts that are not confirmed and have images
    old_receipts = db.query(Receipt).filter(
        Receipt.user_id == current_user.id,
        Receipt.created_at < cutoff_date,
        Receipt.status.in_(["pending", "reviewed"]),
        Receipt.image_path.isnot(None)
    ).all()

    deleted_count = 0
    failed_count = 0

    for receipt in old_receipts:
        try:
            if receipt.image_path and os.path.exists(receipt.image_path):
                os.remove(receipt.image_path)
                print(f"✅ Deleted old image for receipt {receipt.id}: {receipt.image_path}")
            # Clear the image_path in database
            receipt.image_path = None
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  Could not delete image for receipt {receipt.id}: {e}")
            failed_count += 1

    db.commit()

    return {
        "message": f"Cleanup complete",
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "cutoff_date": cutoff_date.isoformat()
    }


@router.post("/images/all-confirmed")
def cleanup_all_confirmed_images(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete images for all confirmed receipts (one-time cleanup).

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Summary of cleanup results
    """
    confirmed_receipts = db.query(Receipt).filter(
        Receipt.user_id == current_user.id,
        Receipt.status == "confirmed",
        Receipt.image_path.isnot(None)
    ).all()

    deleted_count = 0
    failed_count = 0

    for receipt in confirmed_receipts:
        try:
            if receipt.image_path and os.path.exists(receipt.image_path):
                os.remove(receipt.image_path)
                print(f"✅ Deleted image for confirmed receipt {receipt.id}: {receipt.image_path}")
            # Clear the image_path in database
            receipt.image_path = None
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  Could not delete image for receipt {receipt.id}: {e}")
            failed_count += 1

    db.commit()

    return {
        "message": f"All confirmed receipt images cleaned up",
        "deleted_count": deleted_count,
        "failed_count": failed_count
    }


def cleanup_orphaned_images():
    """
    Cleanup orphaned image files (files that exist but no receipt references them).
    This should be called periodically (e.g., via cron job).
    """
    storage_path = settings.image_storage_path

    if not os.path.exists(storage_path):
        return {"cleaned": 0, "message": "Storage path does not exist"}

    from app.database.connection import SessionLocal
    db = SessionLocal()

    try:
        # Get all image paths from database
        receipt_image_paths = set(
            r[0] for r in db.query(Receipt.image_path).filter(
                Receipt.image_path.isnot(None)
            ).all()
        )

        # Find all files in storage directory
        cleaned = 0
        for filename in os.listdir(storage_path):
            file_path = os.path.join(storage_path, filename)

            if os.path.isfile(file_path):
                # Check if this file is referenced by any receipt
                if file_path not in receipt_image_paths:
                    try:
                        os.remove(file_path)
                        print(f"✅ Deleted orphaned image: {file_path}")
                        cleaned += 1
                    except Exception as e:
                        print(f"⚠️  Could not delete orphaned image {file_path}: {e}")

        return {"cleaned": cleaned}
    finally:
        db.close()
