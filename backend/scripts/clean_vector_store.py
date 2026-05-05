#!/usr/bin/env python3
"""
Clean vector store by removing receipts that don't exist in database.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.services.vector_store import get_vector_store
from app.config import settings

def main():
    print("🧹 Cleaning vector store...")

    # Get all IDs from vector store
    vector_store = get_vector_store()
    results = vector_store.search("test", n_results=100)
    vector_ids = [r['id'] for r in results]

    print(f"📦 Vector store has {len(vector_ids)} receipts")

    if len(vector_ids) == 0:
        print("✅ Vector store is already clean!")
        return

    # Get all valid IDs from database
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM receipts"))
        db_ids = set(row[0] for row in result.fetchall())

    print(f"💾 Database has {len(db_ids)} receipts")

    # Find invalid IDs
    invalid_ids = [vid for vid in vector_ids if vid not in db_ids]
    valid_ids = [vid for vid in vector_ids if vid in db_ids]

    print(f"\n✅ Valid IDs in vector store: {len(valid_ids)}")
    print(f"❌ Invalid IDs to remove: {len(invalid_ids)}")

    if invalid_ids:
        print(f"\n🗑️  Removing {len(invalid_ids)} invalid IDs...")
        for vid in invalid_ids:
            try:
                vector_store.collection.delete(ids=[str(vid)])
            except Exception as e:
                print(f"Error deleting ID {vid}: {e}")

        # Verify cleanup
        remaining = vector_store.search("test", n_results=100)
        print(f"\n✅ Cleanup complete! Vector store now has {len(remaining)} receipts")

        # Re-index valid receipts to ensure they're properly stored
        if valid_ids:
            print(f"\n🔄 Re-indexing {len(valid_ids)} valid receipts...")
            with engine.connect() as conn:
                for vid in valid_ids[:10]:  # Limit to first 10 for speed
                    result = conn.execute(text(
                        """SELECT id, sender, receiver, amount, extracted_date, note
                           FROM receipts WHERE id = :id"""
                    ), {"id": vid})
                    row = result.fetchone()

                    if row and (row[1] or row[2] or row[3]):  # Has data
                        receipt_data = {
                            'extracted_date': row[4].isoformat() if row[4] else None,
                            'sender': row[1],
                            'receiver': row[2],
                            'amount': float(row[3]) if row[3] else None,
                            'note': row[5]
                        }
                        vector_store.index_receipt(vid, receipt_data)

            print(f"✅ Re-indexing complete!")
            print(f"📦 Final vector store count: {vector_store.get_count()}")

    else:
        print("✅ Vector store is already clean!")

if __name__ == "__main__":
    main()
