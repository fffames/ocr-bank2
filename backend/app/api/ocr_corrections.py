"""OCR corrections API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from app.services.ocr_correction_service import get_correction_service

router = APIRouter()

class CorrectionAdd(BaseModel):
    """Request model for adding a correction."""
    wrong_text: str
    correct_text: str


class CorrectionUpdate(BaseModel):
    """Request model for updating a correction."""
    correct_text: str


@router.get("/corrections")
async def get_corrections():
    """
    Get all OCR correction mappings.

    Returns:
        Dictionary of all correction mappings
    """
    service = get_correction_service()
    corrections = service.get_corrections()
    return {
        "corrections": corrections,
        "count": len(corrections)
    }


@router.post("/corrections")
async def add_correction(correction: CorrectionAdd):
    """
    Add a new OCR correction mapping.

    Args:
        correction: Correction data with wrong_text and correct_text

    Returns:
        Updated corrections dictionary
    """
    if not correction.wrong_text or not correction.wrong_text.strip():
        raise HTTPException(status_code=400, detail="wrong_text cannot be empty")

    if not correction.correct_text or not correction.correct_text.strip():
        raise HTTPException(status_code=400, detail="correct_text cannot be empty")

    service = get_correction_service()
    corrections = service.add_correction(
        correction.wrong_text.strip(),
        correction.correct_text.strip()
    )

    return {
        "message": f"Added correction: '{correction.wrong_text}' -> '{correction.correct_text}'",
        "corrections": corrections,
        "count": len(corrections)
    }


@router.put("/corrections/{wrong_text}")
async def update_correction(wrong_text: str, correction: CorrectionUpdate):
    """
    Update an existing OCR correction mapping.

    Args:
        wrong_text: The incorrect text to update
        correction: New correct_text value

    Returns:
        Updated corrections dictionary
    """
    service = get_correction_service()

    if wrong_text not in service.get_corrections():
        raise HTTPException(status_code=404, detail=f"Correction '{wrong_text}' not found")

    # Remove old mapping and add new one
    service.remove_correction(wrong_text)
    corrections = service.add_correction(wrong_text, correction.correct_text.strip())

    return {
        "message": f"Updated correction: '{wrong_text}' -> '{correction.correct_text}'",
        "corrections": corrections,
        "count": len(corrections)
    }


@router.delete("/corrections/{wrong_text}")
async def delete_correction(wrong_text: str):
    """
    Delete an OCR correction mapping.

    Args:
        wrong_text: The incorrect text to remove

    Returns:
        Updated corrections dictionary
    """
    service = get_correction_service()

    if wrong_text not in service.get_corrections():
        raise HTTPException(status_code=404, detail=f"Correction '{wrong_text}' not found")

    corrections = service.remove_correction(wrong_text)

    return {
        "message": f"Deleted correction: '{wrong_text}'",
        "corrections": corrections,
        "count": len(corrections)
    }


@router.delete("/corrections")
async def clear_corrections():
    """
    Clear all OCR correction mappings.

    Returns:
        Empty corrections dictionary
    """
    service = get_correction_service()
    corrections = service.clear_corrections()

    return {
        "message": "Cleared all corrections",
        "corrections": corrections,
        "count": 0
    }


@router.post("/corrections/reload")
async def reload_corrections():
    """
    Reload OCR correction mappings from file.

    Returns:
        Updated corrections dictionary
    """
    service = get_correction_service()
    corrections = service.reload_corrections()

    return {
        "message": f"Reloaded {len(corrections)} corrections from file",
        "corrections": corrections,
        "count": len(corrections)
    }
