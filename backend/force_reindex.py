#!/usr/bin/env python3
"""
Force clear and re-index vector store with transaction types.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.services.vector_store import get_vector_store
from app.config import settings

def main():
    print("🔄 Force re-indexing with transaction types...")

    # Get vector store
    vector_store = get_vector_store()
    collection = vector_store.collection

    # Get all current IDs
    results = collection.get()
    existing_ids = results['ids']

    print(f"📦 Current vector store has {len(existing_ids)} receipts")

    if len(existing_ids) > 0:
        print(f"🗑️  Deleting all {len(existing_ids)} receipts...")
        # Delete one by one
        for receipt_id in existing_ids:
            try:
                collection.delete(ids=[receipt_id])
            except Exception as e:
                print(f"Error deleting {receipt_id}: {e}")

        print("✅ All receipts deleted")

    # Get receipts from database
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, filename, sender, receiver, amount, extracted_date, note, transaction_type
            FROM receipts
            WHERE sender IS NOT NULL
               OR receiver IS NOT NULL
               OR amount IS NOT NULL
            ORDER BY id DESC
        """))
        receipts = result.fetchall()

        print(f"📊 Found {len(receipts)} receipts in database")

        # Index each receipt
        success_count = 0
        for receipt in receipts:
            receipt_id, filename, sender, receiver, amount, extracted_date, note, transaction_type = receipt

            receipt_data = {
                'extracted_date': extracted_date.isoformat() if extracted_date else None,
                'sender': sender,
                'receiver': receiver,
                'amount': float(amount) if amount else None,
                'note': note,
                'transaction_type': transaction_type
            }

            try:
                vector_store.index_receipt(receipt_id, receipt_data)
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to index receipt {receipt_id}: {e}")

        print(f"\n✅ Successfully indexed {success_count}/{len(receipts)} receipts")

    # Verify
    print("\n🔍 Verifying indexed data...")
    results = collection.get(include=['documents', 'metadatas'], limit=2)
    if results['ids']:
        print("Sample indexed receipt:")
        print(f"  ID: {results['ids'][0]}")
        print(f"  Document: {results['documents'][0][:150]}...")
        print(f"  Metadata transaction_type: {results['metadatas'][0].get('transaction_type', 'NOT FOUND')}")

if __name__ == "__main__":
    main()
