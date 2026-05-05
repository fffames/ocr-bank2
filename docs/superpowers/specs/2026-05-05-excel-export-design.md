# Excel Export Feature - Design Specification

**Date:** 2026-05-05
**Author:** Claude Sonnet
**Status:** Approved

---

## Overview

Replace Google Sheets export functionality with direct Excel file downloads. Users can filter receipts by date range, transaction type, and status, then download a `.xlsx` Excel file with separate sheets for payments and income.

**Motivation:** Improve security (remove Google API dependencies), simplify architecture, and provide better user control over their financial data.

---

## Architecture

### Current System (Google Sheets)
- Backend: `/api/export/sheets` endpoint
- Service: `GoogleSheetsService` with OAuth authentication
- Frontend: Export page with Google Sheets integration
- External dependencies: Google Sheets API, gspread, OAuth
- Security concern: API keys and spreadsheet ID exposed

### New System (Excel Export)
- Backend: `/api/export/excel` endpoint
- Library: `openpyxl` for Excel file generation
- Frontend: Export page with filters + download button
- File generation: Server-side, immediate download
- No external dependencies or API keys

---

## Components

### 1. Backend API Endpoint

**New Endpoint:**
```python
@router.get("/excel")
async def export_to_excel(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export receipts to Excel file with filters.
    
    Query Parameters:
        - date_from: Start date filter (YYYY-MM-DD)
        - date_to: End date filter (YYYY-MM-DD)
        - transaction_type: 'sending', 'receiving', or 'all'
        - status: 'pending', 'reviewed', 'confirmed', or 'all'
    
    Returns:
        Excel file (.xlsx) as downloadable response
        Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        Content-Disposition: attachment; filename="OCR_Bank_Export_TIMESTAMP.xlsx"
    """
```

**Logic:**
1. Apply user filter (current_user.id)
2. Apply date range filter if provided
3. Apply transaction type filter if provided
4. Apply status filter if provided
5. Separate receipts by transaction_type
6. Generate Excel file with openpyxl
7. Return file response

### 2. Excel File Structure

**Filename Format:**
```
OCR_Bank_Export_2026-05-05_143022.xlsx
```

**Sheet 1: "Payments"**
- Headers: Date, Sender, Receiver, Amount (THB), Note
- Data: All receipts where transaction_type = 'sending'
- Sorted by: extracted_date DESC

**Sheet 2: "Income"**
- Headers: Date, Sender, Receiver, Amount (THB), Note
- Data: All receipts where transaction_type = 'receiving'
- Sorted by: extracted_date DESC

**Column Data Types:**
- Date: Excel date format (YYYY-MM-DD)
- Amount: Currency format with 2 decimal places
- Text columns: Plain text

### 3. Frontend Export Page

**Location:** `frontend/src/pages/Export.tsx` (replace current Google Sheets export)

**UI Components:**
1. **Filter Form**
   - Date range: Month/year dropdown picker (or date inputs)
   - Transaction type: Select (All / Sending / Receiving)
   - Status: Select (All / Pending / Reviewed / Confirmed)
   - "Apply Filters" button

2. **Download Button**
   - "Download Excel" button
   - Disabled if no receipts match filters
   - Shows loading spinner during generation

3. **Preview**
   - Show count of matching receipts
   - Breakdown: "X payments, Y income"

**API Integration:**
```typescript
const downloadExcel = async (filters: ExportFilters) => {
  const params = new URLSearchParams();
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  if (filters.transaction_type) params.append('transaction_type', filters.transaction_type);
  if (filters.status) params.append('status', filters.status);

  const url = `${API_URL}/api/export/excel?${params.toString()}`;
  
  // Trigger browser download
  window.location.href = url;
};
```

---

## Data Flow

```
User selects filters → Click "Download Excel"
                     ↓
Frontend: GET /api/export/excel?date_from=...&status=...
                     ↓
Backend: Authenticate user (JWT)
                     ↓
Backend: Query receipts with filters
                     ↓
Backend: Separate by transaction_type
                     ↓
Backend: Create Excel file in memory (openpyxl)
         - Sheet "Payments": sending transactions
         - Sheet "Income": receiving transactions
                     ↓
Backend: Return file response
         - Content-Type: application/vnd.openxmlformats...
         - Content-Disposition: attachment; filename=...
                     ↓
Browser: Download file automatically
```

---

## Error Handling

### Backend Errors
- **No receipts found:** Return 404 with message "No receipts match the specified filters"
- **Filter invalid:** Return 400 with validation error details
- **Excel generation error:** Return 500 with error message

### Frontend Errors
- **Network error:** Show toast message "Failed to connect to server"
- **No matching data:** Show message "No receipts found with current filters"
- **Download failed:** Show toast message "Download failed, please try again"

---

## Testing

### Backend Tests
1. **Test basic export** (no filters)
   - Should download Excel with all user's receipts
   - Verify two sheets exist
   - Verify column headers

2. **Test date filter**
   - Export receipts for specific month
   - Verify only receipts in date range included

3. **Test transaction type filter**
   - Export "sending" only → only Payments sheet has data
   - Export "receiving" only → only Income sheet has data

4. **Test status filter**
   - Export "confirmed" only
   - Verify only confirmed receipts included

5. **Test user isolation**
   - User A exports → only User A's receipts
   - User B exports → only User B's receipts

### Frontend Tests
1. **Filter UI**
   - Date picker works
   - Select dropdowns work
   - Apply filters button updates preview

2. **Download button**
   - Button disabled when no results
   - Shows loading during download
   - Triggers browser download

3. **Error states**
   - Shows message for empty results
   - Shows toast for network errors

---

## Dependencies

### Remove
```python
# From backend/requirements.txt:
google-api-python-client>=2.116.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.0
gspread>=6.1.0

# Files to delete:
backend/app/services/google_sheets_service.py
```

### Add
```python
# To backend/requirements.txt:
openpyxl>=3.1.0
```

---

## Migration Steps

1. **Backup current branch** (already done - new branch created)
2. **Remove Google Sheets code**
   - Delete `backend/app/services/google_sheets_service.py`
   - Update imports in `backend/app/api/export.py`
   - Remove Google Sheets dependencies from requirements.txt
3. **Implement Excel export**
   - Add openpyxl to requirements.txt
   - Update `backend/app/api/export.py` with new endpoint
4. **Update frontend**
   - Replace Google Sheets export UI with Excel export UI
   - Remove Google Sheets status check
5. **Test thoroughly**
   - Test all filter combinations
   - Verify Excel file format
   - Test user isolation
6. **Commit changes**

---

## Success Criteria

- ✅ Excel file downloads successfully with all filters
- ✅ Two sheets created correctly (Payments, Income)
- ✅ Columns are properly formatted (date, currency)
- ✅ User isolation works (only own receipts)
- ✅ No Google Sheets dependencies remain
- ✅ All API keys removed from code
- ✅ Download filename auto-generated correctly
- ✅ Browser downloads file automatically

---

**End of Specification**
