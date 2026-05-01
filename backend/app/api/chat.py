from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database.connection import get_db
from app.services.rag_service import get_rag_service

router = APIRouter()


class ChatQuery(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    source_receipts: list
    session_id: str


@router.post("/query", response_model=ChatResponse)
async def query_chat(
    chat_query: ChatQuery,
    db: Session = Depends(get_db)
):
    """
    Query the RAG chatbot with a question about receipts.

    Args:
        chat_query: User query and optional session ID
        db: Database session

    Returns:
        Chatbot response with source receipts
    """
    if not chat_query.query or not chat_query.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Generate session ID if not provided
    session_id = chat_query.session_id or str(uuid.uuid4())

    try:
        rag_service = get_rag_service()
        result = await rag_service.query(
            user_query=chat_query.query,
            session_id=session_id,
            db=db
        )

        # Format source receipts for response
        source_receipts_formatted = []
        for receipt in result["source_receipts"]:
            source_receipts_formatted.append({
                "id": receipt.id,
                "filename": receipt.filename,
                "extracted_date": receipt.extracted_date.isoformat() if receipt.extracted_date else None,
                "extracted_time": receipt.extracted_time.isoformat() if receipt.extracted_time else None,
                "sender": receipt.sender,
                "receiver": receipt.receiver,
                "amount": float(receipt.amount) if receipt.amount else None,
                "note": receipt.note,
                "image_path": receipt.image_path
            })

        return ChatResponse(
            response=result["response"],
            source_receipts=source_receipts_formatted,
            session_id=result["session_id"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat query: {str(e)}"
        )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a session.

    Args:
        session_id: Chat session ID
        db: Database session

    Returns:
        List of chat messages for the session
    """
    try:
        rag_service = get_rag_service()
        history = rag_service.get_chat_history(session_id, db)

        formatted_history = []
        for entry in history:
            formatted_history.append({
                "id": entry.id,
                "user_message": entry.user_message,
                "bot_response": entry.bot_response,
                "context_receipts": entry.context_receipts,
                "created_at": entry.created_at.isoformat(),
                "llm_provider": entry.llm_provider
            })

        return formatted_history

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )
