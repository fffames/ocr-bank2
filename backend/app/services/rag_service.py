from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.llm_interface import get_llm_provider
from app.services.vector_store import get_vector_store
from app.models.receipt import Receipt, ChatHistory
from datetime import datetime
import json


class RAGService:
    """RAG (Retrieval-Augmented Generation) service for chatbot."""

    def __init__(self):
        self.llm_provider = get_llm_provider()
        self.vector_store = get_vector_store()

    async def query(
        self,
        user_query: str,
        session_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process a user query with RAG.

        Args:
            user_query: The user's question
            session_id: Chat session ID for history tracking
            db: Database session

        Returns:
            Dictionary containing response and source receipts
        """
        # Step 1: Retrieve relevant receipts using semantic search
        relevant_receipts = self.vector_store.search(user_query, n_results=10)  # Get more results for filtering

        # Step 2: Fetch full receipt details from database and filter for data quality
        receipt_ids = [r['id'] for r in relevant_receipts]
        all_receipts = db.query(Receipt).filter(Receipt.id.in_(receipt_ids)).all()

        # Filter to only include receipts with actual data
        receipts = [r for r in all_receipts if r.sender or r.receiver or r.amount]

        if not receipts:
            return {
                "response": "I couldn't find any receipts with the information needed to answer your question. Please make sure your receipts have been processed with OCR and contain extracted data like sender, receiver, or amount.",
                "source_receipts": [],
                "session_id": session_id
            }

        # Step 3: Construct context from receipts
        context = self._construct_context(receipts)

        # Step 4: Generate response using LLM
        response = await self.llm_provider.generate_response(user_query, context)

        # Step 5: Save chat history
        filtered_receipt_ids = [r.id for r in receipts]
        self._save_chat_history(session_id, user_query, response, filtered_receipt_ids, db)

        return {
            "response": response,
            "source_receipts": receipts,
            "session_id": session_id
        }

    def _construct_context(self, receipts: List[Receipt]) -> str:
        """Construct context string from receipts."""
        if not receipts:
            return "No receipt data available."

        context_parts = []
        for i, receipt in enumerate(receipts, 1):
            receipt_info = f"Receipt {i}:\n"
            if receipt.extracted_date:
                receipt_info += f"  Date: {receipt.extracted_date}\n"
            if receipt.extracted_time:
                receipt_info += f"  Time: {receipt.extracted_time}\n"
            if receipt.sender:
                receipt_info += f"  From: {receipt.sender}\n"
            if receipt.receiver:
                receipt_info += f"  To: {receipt.receiver}\n"
            if receipt.amount:
                receipt_info += f"  Amount: {receipt.amount} THB\n"
            if receipt.note:
                receipt_info += f"  Note: {receipt.note}\n"
            context_parts.append(receipt_info)

        return "\n".join(context_parts)

    def _save_chat_history(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        context_receipts: List[int],
        db: Session
    ) -> None:
        """Save chat interaction to database."""
        try:
            from app.models.receipt import ChatHistory

            chat_entry = ChatHistory(
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                context_receipts=json.dumps(context_receipts),
                llm_provider=self.llm_provider.__class__.__name__
            )

            db.add(chat_entry)
            db.commit()

        except Exception as e:
            print(f"Error saving chat history: {e}")

    def get_chat_history(self, session_id: str, db: Session) -> List[ChatHistory]:
        """Get chat history for a session."""
        try:
            from app.models.receipt import ChatHistory

            history = db.query(ChatHistory).filter(
                ChatHistory.session_id == session_id
            ).order_by(ChatHistory.created_at).all()

            return history

        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []

    def index_receipt_for_search(self, receipt: Receipt) -> None:
        """Index a receipt for semantic search."""
        receipt_data = {
            'extracted_date': receipt.extracted_date,
            'sender': receipt.sender,
            'receiver': receipt.receiver,
            'amount': receipt.amount,
            'note': receipt.note
        }

        self.vector_store.index_receipt(receipt.id, receipt_data)

    def remove_receipt_from_index(self, receipt_id: int) -> None:
        """Remove a receipt from the search index."""
        self.vector_store.delete_receipt(receipt_id)


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
