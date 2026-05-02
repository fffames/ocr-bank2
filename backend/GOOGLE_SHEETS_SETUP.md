# Google Sheets Export - Setup Guide

## Quick Start Guide

### Step 1: Create Google Cloud Project & Service Account

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Sign in with your Google account

2. **Create a new project**
   - Click "Select a project" → "New Project"
   - Name it: "OCR Bank Export" (or any name)
   - Click "Create"

3. **Enable APIs**
   - Go to "APIs & Services" → "Library"
   - Search and enable:
     - ✅ Google Sheets API
     - ✅ Google Drive API

### Step 2: Create Service Account

1. **Create Service Account**
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Service account name: `ocr-bank-export`
   - Click "Create and Continue"

2. **Grant Roles**
   - Skip this step (we'll share the sheet directly)

3. **Create Key**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Key type: **JSON** (IMPORTANT!)
   - Click "Create"
   - This will download a JSON file

### Step 3: Configure Backend

1. **Place credentials file**
   - Rename the downloaded JSON file to: `credentials.json`
   - Move it to: `backend/config/credentials.json`
   - ✅ Done!

### Step 4: Create Google Sheet

1. **Create new spreadsheet**
   - Go to: https://sheets.google.com
   - Click "Blank" spreadsheet

2. **Get spreadsheet ID**
   - Look at the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
   ```
   - Copy the `YOUR_SPREADSHEET_ID` part

3. **Add to .env file**
   - Open: `backend/.env`
   - Add or update this line:
   ```
   GOOGLE_SHEETS_SPREADSHEET_ID='your-actual-spreadsheet-id'
   ```

### Step 5: Share Sheet with Service Account

1. **Open your credentials.json**
   - Find the `client_email` field
   - Example: `ocr-bank-export@project-name.iam.gserviceaccount.com`

2. **Share your Google Sheet**
   - In your Google Sheet, click "Share"
   - Paste the service account email
   - Set as: **Editor**
   - Click "Send"

### Step 6: Test Export

1. **Start backend** (if not running)
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

2. **Go to Receipts List page**
   - Open: http://localhost:5173/receipts
   - Click "Export All to Sheets" button

3. **Check your Google Sheet**
   - Should see a new worksheet with all your receipts!
   - Columns: ID, Date, Time, Sender, Receiver, Amount, Transaction Type, etc.

---

## Troubleshooting

### Error: "Google credentials file not found"
**Fix**: Make sure `credentials.json` is in `backend/config/` directory

### Error: "google_sheets_spreadsheet_id is not set"
**Fix**: Add `GOOGLE_SHEETS_SPREADSHEET_ID` to your `.env` file

### Error: "APIError: 403" 
**Fix**: Share the Google Sheet with your service account email (Step 5)

### Error: "APIError: 400"
**Fix**: Make sure you enabled both Google Sheets API AND Google Drive API

---

## Features

✅ **Export All Receipts** - All receipts in database
✅ **Export Filtered** - Only currently filtered/searched receipts
✅ **Export Summary** - Statistics overview (total income, expenses, net balance)

**Color Coding**:
- 🟢 Green rows = Receiving money (income)
- 🔴 Red rows = Sending money (expenses)

**Auto-formatting**:
- Thai Baht currency (฿)
- Date formatting
- Frozen header row
- Auto-resized columns
