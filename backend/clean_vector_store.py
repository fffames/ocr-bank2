"""Clean stale entries from vector store and re-index current receipts."""
import sys
import os
import chromadb

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.config import settings

def clean_and_reindex():
    """Clean vector store and re-index all current receipts."""
    print("🧹 Starting vector store cleanup and reindexing...\n")

    # Get database session
    db = next(get_db())

    # Step 1: Delete and recreate the collection (proper cleanup)
    print("🗑️  Deleting and recreating vector store collection...")
    client = chromadb.PersistentClient(path=settings.chromadb_persist_directory)

    # Delete the old collection
    try:
        client.delete_collection("receipts")
        print("✅ Old collection deleted")
    except:
        print("⚠️  Collection didn't exist or couldn't be deleted")

    # Create a new collection
    collection = client.get_or_create_collection(
        name="receipts",
        metadata={"description": "Receipt data for semantic search"}
    )
    print("✅ New collection created\n")

    # Step 2: Get all receipts from database
    receipts = db.query(Receipt).all()
    print(f"📊 Found {len(receipts)} receipts in database")

    if not receipts:
        print("⚠️  No receipts to re-index")
        return

    # Step 3: Re-index each receipt
    print(f"\n📝 Re-indexing receipts...")
    from app.services.vector_store import VectorStore
    vector_store = VectorStore()  # Create new instance with fresh collection

    success_count = 0
    failed_count = 0

    for receipt in receipts:
        try:
            receipt_data = {
                'extracted_date': receipt.extracted_date.isoformat() if receipt.extracted_date else None,
                'sender': receipt.sender,
                'receiver': receipt.receiver,
                'amount': float(receipt.amount) if receipt.amount else None,
                'note': receipt.note,
                'transaction_type': receipt.transaction_type,
                'income_category': receipt.income_category
            }
            vector_store.index_receipt(receipt.id, receipt_data)
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to index receipt {receipt.id}: {e}")
            failed_count += 1

    print(f"\n✅ Re-indexing complete!")
    print(f"   Success: {success_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total in vector store: {vector_store.get_count()}")
    print(f"   Total in database: {len(receipts)}")

    # Verify
    if vector_store.get_count() == len(receipts):
        print("✅ Vector store is now synchronized with database!")
    else:
        print("⚠️  Warning: Count mismatch - some receipts may not be indexed")

if __name__ == "__main__":
    clean_and_reindex()
