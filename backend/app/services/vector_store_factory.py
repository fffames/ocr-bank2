"""Factory for vector store - supports both ChromaDB (local) and Pinecone (cloud)."""
from typing import Union
from app.config import settings


def get_vector_store():
    """
    Get the appropriate vector store implementation based on settings.

    Returns:
        Vector store instance (either ChromaDB or Pinecone)

    Usage:
        from app.services.vector_store_factory import get_vector_store
        vector_store = get_vector_store()
    """
    # Check if Pinecone API key is configured
    if hasattr(settings, 'pinecone_api_key') and settings.pinecone_api_key:
        # Use Pinecone for cloud deployment (free tier compatible)
        from app.services.vector_store_pinecone import get_vector_store_pinecone
        return get_vector_store_pinecone()
    else:
        # Fallback to ChromaDB for local development
        from app.services.vector_store import VectorStore
        # Return a new instance or singleton
        global _chromadb_fallback
        if '_chromadb_fallback' not in globals():
            _chromadb_fallback = VectorStore()
        return _chromadb_fallback


# Singleton for ChromaDB fallback
_chromadb_fallback = None
