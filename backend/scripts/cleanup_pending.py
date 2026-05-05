#!/usr/bin/env python3
"""
Clean up pending receipts that have no extracted data.

These are failed OCR attempts that clutter the database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.models.receipt import Receipt

def cleanup_pending_receipts():
    """Delete all pending receipts with no extracted data."""
    print("🔍 Searching for pending receipts with no data...")

    db = next(get_db())

    # Find all pending receipts with no data
    pending_no_data = db.query(Receipt).filter(
        Receipt.status == 'pending',
        Receipt.sender.is_(None)
    ).all()

    print(f"📊 Found {len(pending_no_data)} pending receipts with no data")

    if len(pending_no_data) == 0:
        print("✅ No cleanup needed!")
        return

    # Show sample of what will be deleted
    print("\nSample of receipts to be deleted:")
    for r in pending_no_data[:5]:
        print(f"  ID {r.id}: {r.filename} (created: {r.created_at})")

    if len(pending_no_data) > 5:
        print(f"  ... and {len(pending_no_data) - 5} more")

    # Confirm deletion
    confirm = input("\n❓ Delete all these pending receipts? (yes/no): ")

    if confirm.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        return

    # Delete each receipt
    deleted_count = 0
    for receipt in pending_no_data:
        try:
            # Delete image file if exists
            import os
            try:
                if os.path.exists(receipt.image_path):
                    os.remove(receipt.image_path)
                    print(f"  🗑️  Deleted image: {receipt.image_path}")
            except Exception as e:
                print(f"  ⚠️  Could not delete image: {e}")

            # Delete database record
            db.delete(receipt)
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Error deleting receipt {receipt.id}: {e}")

    # Commit all deletions
    db.commit()

    print(f"\n✅ Successfully deleted {deleted_count} pending receipts")

    # Show remaining counts
    total_receipts = db.query(Receipt).count()
    print(f"📊 Remaining receipts in database: {total_receipts}")

if __name__ == "__main__":
    cleanup_pending_receipts()
