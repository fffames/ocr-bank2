import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from app.config import settings


class VectorStore:
    """Vector store for semantic search using ChromaDB."""

    def __init__(self):
        # Ensure persist directory exists
        os.makedirs(settings.chromadb_persist_directory, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.chromadb_persist_directory
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="receipts",
            metadata={"description": "Receipt data for semantic search"}
        )

    def _create_searchable_text(self, receipt: Dict[str, Any]) -> str:
        """Create searchable text from receipt data."""
        parts = []

        if receipt.get('extracted_date'):
            parts.append(f"Date: {receipt['extracted_date']}")

        if receipt.get('sender'):
            parts.append(f"From: {receipt['sender']}")

        if receipt.get('receiver'):
            parts.append(f"To: {receipt['receiver']}")

        if receipt.get('amount'):
            parts.append(f"Amount: {receipt['amount']} THB")

        if receipt.get('note'):
            parts.append(f"Note: {receipt['note']}")

        return ". ".join(parts)

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text.

        For now, we'll use a simple approach. In production, you'd want to use
        a proper embedding model like sentence-transformers or an API.
        """
        # Simple character-based embedding (not ideal, but works for demo)
        # In production, replace with: from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # return model.encode(text).tolist()

        # For now, create a simple hash-based embedding
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()

        # Convert to list of floats
        embedding = [float(int(c, 16)) / 16.0 for c in hash_hex[:512]]
        return embedding

    def index_receipt(self, receipt_id: int, receipt_data: Dict[str, Any]) -> None:
        """Index a receipt in the vector store."""
        try:
            text = self._create_searchable_text(receipt_data)
            print(f"📝 Vector store indexing receipt {receipt_id}: {text[:100]}...")

            if not text or text.strip() == ".":
                print(f"⚠️  Receipt {receipt_id} has no searchable text, skipping")
                return

            embedding = self._generate_embedding(text)

            self.collection.add(
                ids=[str(receipt_id)],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "date": str(receipt_data.get('extracted_date', '')),
                    "amount": str(receipt_data.get('amount', 0)),
                    "sender": str(receipt_data.get('sender', '')),
                    "receiver": str(receipt_data.get('receiver', '')),
                }]
            )
            print(f"✅ Successfully indexed receipt {receipt_id}")
        except Exception as e:
            import traceback
            print(f"❌ Error indexing receipt {receipt_id}: {e}")
            traceback.print_exc()

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar receipts."""
        try:
            query_embedding = self._generate_embedding(query)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, receipt_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': int(receipt_id),
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'document': results['documents'][0][i] if results['documents'] and results['documents'][0] else '',
                        'distance': results['distances'][0][i] if results.get('distances') and results['distances'][0] else 0
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []

    def delete_receipt(self, receipt_id: int) -> None:
        """Delete a receipt from the vector store."""
        try:
            self.collection.delete(ids=[str(receipt_id)])
        except Exception as e:
            print(f"Error deleting receipt {receipt_id}: {e}")

    def get_count(self) -> int:
        """Get the number of receipts in the vector store."""
        try:
            return self.collection.count()
        except Exception as e:
            print(f"Error getting count: {e}")
            return 0

    def clear_all(self) -> None:
        """Clear all receipts from the vector store."""
        try:
            count = self.collection.count()
            print(f"🗑️  Clearing {count} receipts from vector store...")
            self.collection.delete(where={})
            print(f"✅ Vector store cleared")
        except Exception as e:
            print(f"Error clearing vector store: {e}")


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
