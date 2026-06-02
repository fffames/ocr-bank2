"""Vector store using Pinecone for semantic search - Free tier compatible."""
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
from app.config import settings


class VectorStorePinecone:
    """Vector store for semantic search using Pinecone (free tier)."""

    def __init__(self):
        """Initialize Pinecone client and index."""
        # Initialize Pinecone client
        self.client = Pinecone(api_key=settings.pinecone_api_key)

        # Index name
        self.index_name = settings.pinecone_index_name

        # Get or create index
        self._ensure_index_exists()

        # Get index reference
        self.index = self.client.Index(self.index_name)

        # Namespace for this application
        self.namespace = "receipts"

        print(f"✅ Pinecone vector store initialized (index: {self.index_name})")

    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists, create if not."""
        try:
            # List existing indexes
            existing_indexes = [index["name"] for index in self.client.list_indexes()]

            if self.index_name not in existing_indexes:
                print(f"📝 Creating new Pinecone index: {self.index_name}")
                self.client.create_index(
                    name=self.index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                print(f"✅ Index '{self.index_name}' created successfully")
            else:
                print(f"✅ Using existing index: {self.index_name}")

        except Exception as e:
            print(f"⚠️  Error ensuring index exists: {e}")
            # Continue anyway - index might exist but we can't list it

    def _create_searchable_text(self, receipt: Dict[str, Any]) -> str:
        """Create searchable text from receipt data."""
        parts = []

        # Add transaction type first (most important for LLM understanding)
        if receipt.get('transaction_type'):
            trans_type = receipt['transaction_type']
            if trans_type == 'sending':
                parts.append("Transaction type: Sending money (payment/expense)")
            elif trans_type == 'receiving':
                parts.append("Transaction type: Receiving money (income)")
            else:
                parts.append(f"Transaction type: {trans_type}")

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
        """Generate embedding for text using sentence-transformers."""
        # Lazy import to avoid startup overhead
        if not hasattr(self, '_embedding_model'):
            from sentence_transformers import SentenceTransformer
            # Use tiny model for free tier compatibility (80MB vs 500MB)
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded lightweight sentence-transformers model (all-MiniLM-L6-v2)")

        # Generate embedding
        embedding = self._embedding_model.encode(text, show_progress_bar=False).tolist()
        return embedding

    def index_receipt(self, receipt_id: int, receipt_data: Dict[str, Any]) -> None:
        """Index a receipt in Pinecone."""
        try:
            text = self._create_searchable_text(receipt_data)
            print(f"📝 Pinecone indexing receipt {receipt_id}: {text[:100]}...")

            if not text or text.strip() == ".":
                print(f"⚠️  Receipt {receipt_id} has no searchable text, skipping")
                return

            embedding = self._generate_embedding(text)

            # Upsert to Pinecone
            self.index.upsert(
                vectors=[
                    {
                        "id": str(receipt_id),
                        "values": embedding,
                        "metadata": {
                            "text": text,
                            "date": str(receipt_data.get('extracted_date', '')),
                            "amount": str(receipt_data.get('amount', 0)),
                            "sender": str(receipt_data.get('sender', '')),
                            "receiver": str(receipt_data.get('receiver', '')),
                            "transaction_type": str(receipt_data.get('transaction_type', 'unknown')),
                        }
                    }
                ],
                namespace=self.namespace
            )
            print(f"✅ Successfully indexed receipt {receipt_id} in Pinecone")

        except Exception as e:
            import traceback
            print(f"❌ Error indexing receipt {receipt_id} in Pinecone: {e}")
            traceback.print_exc()

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar receipts using Pinecone."""
        try:
            query_embedding = self._generate_embedding(query)

            results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                namespace=self.namespace,
                include_metadata=True
            )

            # Format results
            formatted_results = []
            if results['matches']:
                for match in results['matches']:
                    formatted_results.append({
                        'id': int(match['id']),
                        'metadata': match.get('metadata', {}),
                        'document': match['metadata'].get('text', ''),
                        'distance': 1 - match.get('score', 0),  # Convert score to distance
                        'score': match.get('score', 0)
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching Pinecone: {e}")
            return []

    def delete_receipt(self, receipt_id: int) -> None:
        """Delete a receipt from Pinecone."""
        try:
            self.index.delete(
                ids=[str(receipt_id)],
                namespace=self.namespace
            )
            print(f"✅ Deleted receipt {receipt_id} from Pinecone")

        except Exception as e:
            print(f"⚠️  Could not delete receipt {receipt_id} from Pinecone: {e}")

    def get_count(self) -> int:
        """Get the number of receipts in Pinecone."""
        try:
            # Pinecone doesn't have a direct count method for namespaces
            # We'll query with a top_k of 1 and return total count if available
            # Otherwise return 0 (index might be empty)
            try:
                stats = self.index.describe_index_stats()
                # Get count for our namespace
                namespace_stats = stats.get('namespaces', {}).get(self.namespace, {})
                return namespace_stats.get('vector_count', 0)
            except:
                return 0

        except Exception as e:
            print(f"Error getting count from Pinecone: {e}")
            return 0

    def clear_all(self) -> None:
        """Clear all receipts from Pinecone namespace."""
        try:
            # Delete all vectors in the namespace
            self.index.delete(
                delete_all=True,
                namespace=self.namespace
            )
            print(f"✅ Cleared all receipts from Pinecone namespace: {self.namespace}")

        except Exception as e:
            print(f"Error clearing Pinecone namespace: {e}")


# Singleton instance
_vector_store_pinecone = None


def get_vector_store_pinecone() -> VectorStorePinecone:
    """Get or create Pinecone vector store singleton."""
    global _vector_store_pinecone
    if _vector_store_pinecone is None:
        _vector_store_pinecone = VectorStorePinecone()
    return _vector_store_pinecone
