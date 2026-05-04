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
        print(f"\n🔍 RAG Query: {user_query}")

        # Detect SQL aggregation questions (can be answered with database query)
        sql_aggregate_patterns = [
            'most expensive', 'cheapest', 'highest', 'lowest', 'maximum', 'minimum', 'max', 'min',
            'average', 'mean', 'typical',
            'ราคาแพงสุด', 'ราคาถูกสุด', 'สูงสุด', 'ต่ำสุด', 'มากที่สุด', 'น้อยที่สุด'
        ]
        is_sql_aggregate = any(pattern in user_query.lower() for pattern in sql_aggregate_patterns)

        # Detect fetch-all questions (need all receipts for LLM to process)
        fetch_all_keywords = ['total', 'sum', 'all', 'overall', 'complete', 'every', 'aggregate', 'รวม', 'ทั้งหมด', 'โดยรวม']
        is_fetch_all = any(keyword in user_query.lower() for keyword in fetch_all_keywords)

        receipts = []
        if is_sql_aggregate:
            # Use SQL to calculate aggregates directly - fast and accurate
            print(f"📊 SQL aggregate query detected - using database aggregation")
            from sqlalchemy import func

            result = {}

            # Most expensive payment
            if any(p in user_query.lower() for p in ['most expensive', 'highest', 'maximum', 'ราคาแพงสุด', 'สูงสุด']):
                most_expensive = db.query(Receipt).filter(
                    Receipt.amount.isnot(None)
                ).order_by(Receipt.amount.desc()).first()
                if most_expensive:
                    result['most_expensive'] = most_expensive
                    receipts.append(most_expensive)

            # Cheapest payment
            if any(p in user_query.lower() for p in ['cheapest', 'lowest', 'minimum', 'ราคาถูกสุด', 'ต่ำสุด']):
                cheapest = db.query(Receipt).filter(
                    Receipt.amount.isnot(None)
                ).order_by(Receipt.amount.asc()).first()
                if cheapest:
                    result['cheapest'] = cheapest
                    receipts.append(cheapest)

            # Average/mean
            if any(p in user_query.lower() for p in ['average', 'mean', 'average amount', 'mean amount', 'เฉลี่ย']):
                avg_result = db.query(func.avg(Receipt.amount)).filter(
                    Receipt.amount.isnot(None)
                ).scalar()
                if avg_result:
                    result['average'] = float(avg_result)

            print(f"✅ SQL aggregation complete: {list(result.keys())}")

            # If we found results via SQL, return them directly (skip LLM for simple queries)
            if result and not is_fetch_all:
                # Format response from SQL results
                response_parts = []
                if 'most_expensive' in result:
                    r = result['most_expensive']
                    response_parts.append(f"Your most expensive payment was {r.amount} THB to {r.receiver or 'unknown'} on {r.extracted_date or 'unknown date'}.")
                if 'cheapest' in result:
                    r = result['cheapest']
                    response_parts.append(f"Your cheapest payment was {r.amount} THB to {r.receiver or 'unknown'} on {r.extracted_date or 'unknown date'}.")
                if 'average' in result:
                    response_parts.append(f"Your average payment amount is {result['average']:.2f} THB.")

                return {
                    "response": " ".join(response_parts),
                    "source_receipts": receipts,
                    "session_id": session_id
                }

        elif is_fetch_all:
            print(f"📊 Fetch-all query detected - getting ALL receipts from database")
            # For aggregate queries, get ALL receipts with data from database (no limit)
            all_receipts = db.query(Receipt).filter(
                (Receipt.sender.isnot(None)) | (Receipt.receiver.isnot(None)) | (Receipt.amount.isnot(None))
            ).order_by(Receipt.extracted_date.desc()).all()
            receipts = all_receipts
            print(f"✅ Fetched {len(receipts)} receipts from database")
        else:
            # Semantic search - use vector store for finding relevant receipts
            print(f"🔍 Semantic search - using vector store")
            relevant_receipts = self.vector_store.search(user_query, n_results=50)
            print(f"📊 Vector store returned {len(relevant_receipts)} results")
            for r in relevant_receipts[:3]:
                print(f"   - ID {r['id']}: {r['document'][:60]}...")

            # Step 2: Fetch full receipt details from database for semantic search results
            receipt_ids = [r['id'] for r in relevant_receipts]
            print(f"🔑 Fetching receipts with IDs: {receipt_ids[:5]}...")

            all_receipts = db.query(Receipt).filter(Receipt.id.in_(receipt_ids)).all()
            print(f"💾 Database returned {len(all_receipts)} receipts")

            # Filter to only include receipts with actual data
            receipts = [r for r in all_receipts if r.sender or r.receiver or r.amount]
            print(f"✅ After filtering for data: {len(receipts)} receipts")

            for r in receipts[:3]:
                print(f"   - ID {r.id}: sender={bool(r.sender)}, receiver={bool(r.receiver)}, amount={bool(r.amount)}")

        if not receipts:
            return {
                "response": "I couldn't find any receipts with the information needed to answer your question. Please make sure your receipts have been processed with OCR and contain extracted data like sender, receiver, or amount.",
                "source_receipts": [],
                "session_id": session_id
            }

        # Step 3: Construct context from receipts
        context = self._construct_context(receipts, is_aggregate_query=is_fetch_all)

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

    def _construct_context(self, receipts: List[Receipt], is_aggregate_query: bool = False) -> str:
        """Construct context string from receipts.

        Args:
            receipts: List of receipts
            is_aggregate_query: Whether this is an aggregate query (affects format)

        Returns:
            Formatted context string
        """
        if not receipts:
            return "No receipt data available."

        if is_aggregate_query:
            # Compact format for aggregate queries (focus on amounts and transaction types)
            context_parts = [f"I have {len(receipts)} receipts with transaction data:\n"]

            for i, receipt in enumerate(receipts, 1):
                receipt_info = f"{i}. "
                if receipt.extracted_date:
                    receipt_info += f"Date: {receipt.extracted_date}, "
                if receipt.transaction_type:
                    receipt_info += f"Type: {receipt.transaction_type}, "
                if receipt.amount:
                    receipt_info += f"Amount: {receipt.amount} THB, "
                if receipt.sender:
                    receipt_info += f"From: {receipt.sender[:50]}, "
                if receipt.receiver:
                    receipt_info += f"To: {receipt.receiver[:50]}"
                context_parts.append(receipt_info.strip())

            return "\n".join(context_parts)
        else:
            # Verbose format for specific queries
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
