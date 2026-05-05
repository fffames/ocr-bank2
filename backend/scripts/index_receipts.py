#!/usr/bin/env python3
"""Index all existing receipts into the vector store for chat functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.services.vector_store import get_vector_store

def index_all_receipts():
    """Index all receipts from the database into the vector store."""
    print("🔄 Starting receipt indexing...")

    # Get database session
    db = next(get_db())

    # Get only receipts with actual data
    from sqlalchemy import or_
    receipts = db.query(Receipt).filter(
        or_(
            Receipt.sender.isnot(None),
            Receipt.receiver.isnot(None),
            Receipt.amount.isnot(None)
        )
    ).all()
    print(f"📊 Found {len(receipts)} receipts with actual data")

    # Get vector store
    vector_store = get_vector_store()

    # Clear existing collection to avoid duplicates
    try:
        vector_store.client.delete_collection("receipts")
        vector_store.collection = vector_store.client.get_or_create_collection(
            name="receipts",
            metadata={"description": "Receipt data for semantic search"}
        )
        print("🗑️  Cleared old index")
    except Exception as e:
        print(f"⚠️  Could not clear old collection: {e}")

    # Index each receipt
    indexed_count = 0
    for receipt in receipts:
        try:
            receipt_data = {
                'extracted_date': receipt.extracted_date,
                'sender': receipt.sender,
                'receiver': receipt.receiver,
                'amount': receipt.amount,
                'note': receipt.note
            }
            vector_store.index_receipt(receipt.id, receipt_data)
            indexed_count += 1
            print(f"✅ Indexed receipt {receipt.id}: {receipt.filename} - {receipt.sender or 'No sender'} → {receipt.receiver or 'No receiver'} ({receipt.amount or 0} THB)")
        except Exception as e:
            print(f"❌ Error indexing receipt {receipt.id}: {e}")

    print(f"\n🎉 Successfully indexed {indexed_count} receipts with data")
    print("💬 Chat functionality should now work with better results!")

if __name__ == "__main__":
    index_all_receipts()
