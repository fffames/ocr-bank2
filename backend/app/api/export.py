"""Google Sheets export API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.services.google_sheets_service import get_google_sheets_service

router = APIRouter()


class ExportRequest(BaseModel):
    """Request model for exporting receipts."""
    receipt_ids: Optional[List[int]] = None  # None = export all
    export_type: str = "receipts"  # "receipts" or "summary"


@router.post("/sheets")
async def export_to_sheets(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export receipts to Google Sheets.

    Args:
        request: Export request with receipt IDs and export type
        db: Database session

    Returns:
        Export result with spreadsheet URL
    """
    try:
        service = get_google_sheets_service()

        if request.export_type == "summary":
            # Export summary statistics
            result = service.export_summary(db)

        else:
            # Export specific receipts or all
            if request.receipt_ids:
                receipts = db.query(Receipt).filter(Receipt.id.in_(request.receipt_ids)).all()
            else:
                receipts = db.query(Receipt).all()

            if not receipts:
                raise HTTPException(status_code=404, detail="No receipts found to export")

            result = service.export_receipts(receipts)

        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Export failed'))

        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/status")
async def get_export_status():
    """
    Check if Google Sheets integration is configured.

    Returns:
        Configuration status
    """
    from app.config import settings
    import os

    return {
        "configured": bool(settings.google_sheets_spreadsheet_id),
        "credentials_exist": os.path.exists(settings.google_sheets_credentials_path),
        "spreadsheet_id": settings.google_sheets_spreadsheet_id if settings.google_sheets_spreadsheet_id else None
    }
