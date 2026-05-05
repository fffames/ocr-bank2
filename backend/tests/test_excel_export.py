"""Tests for Excel export functionality."""
import pytest
from datetime import date, datetime
from io import BytesIO
from app.services.excel_export_service import get_excel_export_service
from app.models.receipt import Receipt
from app.models.user import User


def test_excel_service_singleton():
    """Test that Excel service singleton works."""
    service = get_excel_export_service()
    assert service is not None
    assert service.__class__.__name__ == "ExcelExportService"


def test_export_empty_receipts(db_session):
    """Test exporting empty receipt list."""
    service = get_excel_export_service()

    # Should handle empty list gracefully
    excel_data = service.export_receipts([])

    assert excel_data is not None
    assert len(excel_data) > 0  # Excel files have minimum size


def test_export_sample_receipts(db_session, test_user, sample_receipts):
    """Test exporting sample receipts."""
    service = get_excel_export_service()

    receipts = sample_receipts[:3]
    excel_data = service.export_receipts(receipts)

    assert excel_data is not None
    assert len(excel_data) > 100  # Valid Excel file has content
