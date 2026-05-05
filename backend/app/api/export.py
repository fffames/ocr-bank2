"""Excel export API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.services.auth_service import get_current_active_user
from app.services.excel_export_service import get_excel_export_service

router = APIRouter()


@router.get("/excel")
async def export_to_excel(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    transaction_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export receipts to Excel file with filters.

    Args:
        date_from: Start date filter (YYYY-MM-DD)
        date_to: End date filter (YYYY-MM-DD)
        transaction_type: 'sending', 'receiving', or 'all'
        status: 'pending', 'reviewed', 'confirmed', or 'all'
        current_user: Authenticated user
        db: Database session

    Returns:
        Excel file (.xlsx) as downloadable response
    """
    try:
        # Build query with user filter
        query = db.query(Receipt).filter(Receipt.user_id == current_user.id)

        # Apply date range filter
        if date_from:
            query = query.filter(Receipt.extracted_date >= date_from)
        if date_to:
            # Include the full day by adding one day and using < instead of <=
            from datetime import timedelta
            date_to_end = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Receipt.extracted_date < date_to_end)

        # Apply transaction type filter
        if transaction_type and transaction_type != "all":
            query = query.filter(Receipt.transaction_type == transaction_type)

        # Apply status filter
        if status and status != "all":
            query = query.filter(Receipt.status == status)

        # Fetch filtered receipts
        receipts = query.order_by(Receipt.extracted_date.desc()).all()

        if not receipts:
            raise HTTPException(
                status_code=404,
                detail="No receipts found matching the specified filters"
            )

        # Generate Excel file
        service = get_excel_export_service()
        excel_data = service.export_receipts(receipts)

        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"OCR_Bank_Export_{timestamp}.xlsx"

        # Return file as downloadable response
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Excel file: {str(e)}"
        )


@router.get("/status")
async def get_export_status():
    """
    Check if Excel export is available.

    Returns:
        Export service status
    """
    try:
        from app.services.excel_export_service import get_excel_export_service, EXCEL_AVAILABLE
        return {
            "available": EXCEL_AVAILABLE,
            "format": "Excel (.xlsx)",
            "features": ["date_range", "transaction_type", "status"]
        }
    except ImportError:
        return {
            "available": False,
            "error": "Excel export service not available"
        }
