"""Google Sheets export service for OCR Bank receipts."""
import os
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

from app.models.receipt import Receipt
from app.config import settings


class GoogleSheetsService:
    """Service for exporting receipts to Google Sheets."""

    def __init__(self):
        if not GOOGLE_SHEETS_AVAILABLE:
            raise ImportError("gspread library not installed. Run: pip install gspread")

        # Check if credentials file exists
        if not os.path.exists(settings.google_sheets_credentials_path):
            raise FileNotFoundError(
                f"Google credentials file not found: {settings.google_sheets_credentials_path}\n"
                "Please download your Google Service Account credentials JSON file "
                "and place it in the config directory."
            )

        if not settings.google_sheets_spreadsheet_id:
            raise ValueError(
                "google_sheets_spreadsheet_id is not set in .env file.\n"
                "Please add: GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id'"
            )

        # Authenticate with Google Sheets
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file(
            settings.google_sheets_credentials_path,
            scopes=scope
        )

        self.client = gspread.authorize(creds)
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id

    def export_receipts(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """
        Export receipts to Google Sheets.

        Args:
            receipts: List of receipt objects to export

        Returns:
            Dictionary with export status and details
        """
        try:
            # Open spreadsheet
            sh = self.client.open_by_key(self.spreadsheet_id)

            # Create or clear worksheet
            worksheet_name = f"Receipts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            try:
                # Try to create new worksheet
                worksheet = sh.add_worksheet(title=worksheet_name, rows="1000", cols="26")
            except gspread.exceptions.APIError:
                # If worksheet already exists, use the first one
                worksheet = sh.sheet1
                worksheet.clear()
                worksheet_name = worksheet.title

            # Define headers
            headers = [
                'ID',
                'Date',
                'Time',
                'Sender',
                'Receiver',
                'Amount (THB)',
                'Transaction Type',
                'Status',
                'Filename',
                'Note'
            ]

            # Write headers
            worksheet.update('A1', [headers], value_input_option='USER_ENTERED')

            # Format headers
            worksheet.format('A1:K1', {
                'backgroundColor': {
                    'red': 0.2,
                    'green': 0.4,
                    'blue': 0.8
                },
                'textFormat': {
                    'bold': True,
                    'foregroundColor': {
                        'red': 1.0,
                        'green': 1.0,
                        'blue': 1.0
                    }
                }
            })

            # Prepare data rows
            rows = []
            for receipt in receipts:
                row = [
                    receipt.id,
                    receipt.extracted_date.strftime('%Y-%m-%d') if receipt.extracted_date else '',
                    str(receipt.extracted_time) if receipt.extracted_time else '',
                    receipt.sender or '',
                    receipt.receiver or '',
                    float(receipt.amount) if receipt.amount else 0,
                    receipt.transaction_type or 'unknown',
                    receipt.status or 'pending',
                    receipt.filename or '',
                    receipt.note or ''
                ]
                rows.append(row)

            if rows:
                # Write data to sheet
                worksheet.update('A2', rows, value_input_option='USER_ENTERED')

                # Format amount column as currency
                worksheet.format('F2:F' + str(len(rows) + 1), {
                    'numberFormat': {
                        'type': 'CURRENCY',
                        'pattern': '"฿"#,##0.00'
                    }
                })

                # Color code transaction types
                for i, row in enumerate(rows, start=2):
                    if row[6] == 'receiving':
                        # Green for income
                        worksheet.format(f'A{i}:K{i}', {
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 1.0,
                                'blue': 0.9
                            }
                        })
                    elif row[6] == 'sending':
                        # Red for expenses
                        worksheet.format(f'A{i}:K{i}', {
                            'backgroundColor': {
                                'red': 1.0,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        })

            # Freeze header row
            worksheet.freeze(1)

            # Note: columns_auto_resize() is not available in current gspread version
            # Google Sheets auto-sizes columns automatically

            return {
                'success': True,
                'worksheet': worksheet_name,
                'rows_exported': len(rows),
                'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def export_summary(self, db: Session) -> Dict[str, Any]:
        """
        Export summary statistics to Google Sheets.

        Args:
            db: Database session

        Returns:
            Dictionary with export status
        """
        try:
            # Get all receipts
            receipts = db.query(Receipt).all()

            # Calculate summary
            summary = self._calculate_summary(receipts)

            # Open spreadsheet
            sh = self.client.open_by_key(self.spreadsheet_id)

            # Create summary worksheet
            worksheet_name = f"Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            try:
                worksheet = sh.add_worksheet(title=worksheet_name, rows="100", cols="26")
            except gspread.exceptions.APIError:
                worksheet = sh.get_worksheet(0)
                worksheet.clear()
                worksheet_name = worksheet.title

            # Write summary data
            summary_data = [
                ['Metric', 'Value'],
                ['Total Receipts', summary['total_receipts']],
                ['Total Income', f"฿{summary['total_income']:.2f}"],
                ['Total Expenses', f"฿{summary['total_expenses']:.2f}"],
                ['Net Balance', f"฿{summary['net_balance']:.2f}"],
                ['Sending Transactions', summary['sending_count']],
                ['Receiving Transactions', summary['receiving_count']],
                [],
                ['Breakdown by Transaction Type', ''],
                ['Sending (Expenses)', summary['sending_count']],
                ['Receiving (Income)', summary['receiving_count']],
                ['Unknown', summary['unknown_count']]
            ]

            worksheet.update('A1', summary_data, value_input_option='USER_ENTERED')

            # Format headers
            worksheet.format('A1:B1', {
                'backgroundColor': {
                    'red': 0.2,
                    'green': 0.4,
                    'blue': 0.8
                },
                'textFormat': {
                    'bold': True,
                    'foregroundColor': {
                        'red': 1.0,
                        'green': 1.0,
                        'blue': 1.0
                    }
                }
            })

            return {
                'success': True,
                'worksheet': worksheet_name,
                'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_summary(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """Calculate summary statistics from receipts."""
        sending = [r for r in receipts if r.transaction_type == 'sending']
        receiving = [r for r in receipts if r.transaction_type == 'receiving']

        total_income = sum((r.amount or 0) for r in receiving)
        total_expenses = sum((r.amount or 0) for r in sending)

        return {
            'total_receipts': len(receipts),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': total_income - total_expenses,
            'sending_count': len(sending),
            'receiving_count': len(receiving),
            'unknown_count': len(receipts) - len(sending) - len(receiving)
        }


def get_google_sheets_service() -> GoogleSheetsService:
    """Factory function to get Google Sheets service instance."""
    return GoogleSheetsService()
