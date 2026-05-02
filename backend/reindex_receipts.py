#!/usr/bin/env python3
"""
Re-index all receipts from PostgreSQL into ChromaDB vector store.
Run this script to populate the vector store with existing receipt data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.vector_store import get_vector_store
from app.config import settings

def main():
    print("🔄 Starting receipt re-indexing...")

    # Connect to PostgreSQL
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Get all receipts with actual data
        query = text("""
            SELECT id, filename, sender, receiver, amount, extracted_date, note
            FROM receipts
            WHERE sender IS NOT NULL
               OR receiver IS NOT NULL
               OR amount IS NOT NULL
            ORDER BY id DESC
        """)

        result = db.execute(query)
        receipts = result.fetchall()

        print(f"📊 Found {len(receipts)} receipts with data in PostgreSQL")

        if len(receipts) == 0:
            print("⚠️  No receipts found to index!")
            return

        # Get vector store
        vector_store = get_vector_store()

        # Check current count
        current_count = vector_store.get_count()
        print(f"📦 Current vector store count: {current_count}")

        # Ask user if they want to clear and re-index
        if current_count > 0:
            response = input(f"\nVector store already has {current_count} receipts. Clear and re-index? (y/N): ")
            if response.lower() == 'y':
                vector_store.clear_all()
            else:
                print("ℹ️  Will add to existing index (may have duplicates)")

        # Index each receipt
        success_count = 0
        for receipt in receipts:
            receipt_id, filename, sender, receiver, amount, extracted_date, note = receipt

            receipt_data = {
                'extracted_date': extracted_date.isoformat() if extracted_date else None,
                'sender': sender,
                'receiver': receiver,
                'amount': float(amount) if amount else None,
                'note': note
            }

            try:
                vector_store.index_receipt(receipt_id, receipt_data)
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to index receipt {receipt_id}: {e}")

        print(f"\n✅ Successfully indexed {success_count}/{len(receipts)} receipts")
        print(f"📦 New vector store count: {vector_store.get_count()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
