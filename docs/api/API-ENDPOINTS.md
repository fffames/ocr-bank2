# API Endpoints - Quick Reference

## Templates API

Base URL: `http://localhost:8000`

### List All Templates
```bash
GET /api/templates/
```

**Response:**
```json
[
  {
    "template_id": "krungthai_kplus",
    "bank_name": "Krungthai Bank (K+)",
    "description": "K+ mobile banking receipt format",
    "num_zones": 6,
    "image_size": [990, 1409]
  }
]
```

### Create New Template
```bash
POST /api/templates/
Content-Type: application/json

{
  "template_id": "kbank",
  "bank_name": "KBank",
  "description": "KBank mBanking receipt",
  "image_size": [1080, 1920],
  "detection_keywords": ["KBank", "KBANK", "K ธนาคาร"],
  "zones": [
    {
      "id": "zone-1",
      "field_name": "date",
      "parser_type": "thai_date",
      "x_percent": 5.0,
      "y_percent": 8.0,
      "width_percent": 35.0,
      "height_percent": 6.0,
      "required": true
    }
  ]
}
```

### Get Specific Template
```bash
GET /api/templates/{template_id}
```

### Delete Template
```bash
DELETE /api/templates/{template_id}
```

### Test OCR on Zone
```bash
POST /api/templates/test-zone
Content-Type: application/json

{
  "image_data": "data:image/jpeg;base64,/9j/4AAQ...",
  "zone": {
    "id": "zone-1",
    "field_name": "amount",
    "parser_type": "thai_amount",
    "x_percent": 30.0,
    "y_percent": 75.0,
    "width_percent": 65.0,
    "height_percent": 6.0,
    "required": true
  }
}
```

**Response:**
```json
{
  "extracted_text": "3,000.00 บาท"
}
```

## Upload API (with Template OCR)

### Upload Receipt Images
```bash
POST /api/upload/
Content-Type: multipart/form-data

files: [image1.jpg, image2.jpg]
```

**Process:**
1. Try template-based OCR first (fast, free)
2. Fall back to VLM if template fails
3. Save results to database

## Testing with cURL

### Test List Templates
```bash
curl http://localhost:8000/api/templates/
```

### Test Create Template
```bash
curl -X POST http://localhost:8000/api/templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "test_template",
    "bank_name": "Test Bank",
    "description": "Test template",
    "image_size": [1000, 1500],
    "detection_keywords": ["test"],
    "zones": []
  }'
```

### Test Get Template
```bash
curl http://localhost:8000/api/templates/krungthai_kplus
```

### Test Delete Template
```bash
curl -X DELETE http://localhost:8000/api/templates/test_template
```

## Common Issues

### 404 Not Found
- Ensure backend server is running: `python -m uvicorn app.main:app --reload`
- Check that templates router is included in `app/main.py`

### CORS Errors
- Check CORS origins in `app/main.py`
- Should include: `http://localhost:5173` and `http://localhost:3000`

### Template Save Fails
- Check templates directory exists: `backend/app/templates/`
- Verify template_id is unique
- Ensure all zones have required fields

### OCR Test Fails
- Ensure image_data is valid base64 string
- Check that zone coordinates are valid (0-100%)
- Verify Tesseract is installed: `tesseract --version`
