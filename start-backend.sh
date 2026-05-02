#!/bin/bash

echo "🚀 Starting OCR Bank Backend Server..."
echo ""

cd /Users/boonkerdinchoi/Downloads/year\ 4/ocr_bank/ocr-bank2/backend

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"
echo "📦 Starting FastAPI server on http://localhost:8000"
echo ""
echo "Available endpoints:"
echo "  - GET  /api/templates/           (List all templates)"
echo "  - POST /api/templates/           (Create new template)"
echo "  - GET  /api/templates/{id}       (Get specific template)"
echo "  - DELETE /api/templates/{id}     (Delete template)"
echo "  - POST /api/templates/test-zone  (Test OCR on zone)"
echo ""
echo "🔥 Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
