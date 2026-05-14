# Image Cleanup API

## Overview

Receipt images are now automatically deleted after confirmation to save storage space. The OCR data is already saved in the database, so the image is no longer needed.

## How It Works

1. **Upload**: Image is temporarily stored at `/tmp/ocr_images/`
2. **OCR Processing**: Image is processed to extract receipt data
3. **User Reviews**: User views and edits the extracted data (image still available for reference)
4. **Confirmation**: When user clicks "Confirm" or status changes to `confirmed`, the image is deleted
5. **Database**: Receipt data remains in database with `image_path` set to `NULL`

## New Endpoints

### 1. Cleanup Old Unconfirmed Images

```http
POST /api/cleanup/images/old?days_old=7
```

Deletes images for receipts older than N days that are still in `pending` or `reviewed` status.

**Parameters:**
- `days_old` (optional, default: 7) - Delete images older than this many days

**Example:**
```bash
curl -X POST "https://your-app.railway.app/api/cleanup/images/old?days_old=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "Cleanup complete",
  "deleted_count": 15,
  "failed_count": 0,
  "cutoff_date": "2025-05-07T12:00:00"
}
```

### 2. Cleanup All Confirmed Receipt Images (One-time)

```http
POST /api/cleanup/images/all-confirmed
```

Deletes images for ALL confirmed receipts. Use this to clean up existing data after first deployment.

**Example:**
```bash
curl -X POST "https://your-app.railway.app/api/cleanup/images/all-confirmed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "All confirmed receipt images cleaned up",
  "deleted_count": 142,
  "failed_count": 2
}
```

## Automatic Cleanup on Confirmation

Images are automatically deleted when:
- User clicks "Confirm" button → `POST /api/receipts/{id}/confirm`
- User updates status to "confirmed" → `PUT /api/receipts/{id}` with `status: "confirmed"`

## Database Migration

After deploying, run the migration to make `image_path` nullable:

```bash
cd backend
python scripts/migrate_image_path_nullable.py
```

Or using Alembic:
```bash
cd backend
alembic upgrade head
```

## Frontend Considerations

The frontend already handles missing images gracefully:
- `ReceiptsList.tsx` and `Review.tsx` show "Image not found" placeholder when `image_path` is NULL
- No changes needed to frontend code

## Storage Savings

| Image Size | Images per Month | Storage Saved |
|------------|------------------|---------------|
| 500 KB     | 100              | 50 MB         |
| 500 KB     | 500              | 250 MB        |
| 1 MB       | 100              | 100 MB        |

After implementation, confirmed receipts use 0 bytes for image storage.

## Cron Job Setup (Optional)

For automatic periodic cleanup, set up a cron job or use a service like cron-job.org:

```bash
# Run cleanup daily at 2 AM
0 2 * * * curl -X POST "https://your-app.railway.app/api/cleanup/images/old?days_old=7" -H "Authorization: Bearer YOUR_TOKEN"
```
