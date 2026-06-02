FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PaddleOCR, OpenCV, and Tesseract OCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-tha \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/images /app/data/chromadb /app/uploads

# Expose port
EXPOSE 8000

# Try to run migrations, but start the app even if they fail
# The migrate endpoint can be called manually if needed
CMD ["sh", "-c", "alembic upgrade head || echo 'Migration failed - will retry via API' && python -u -c 'import os; from app.main import app; import uvicorn; uvicorn.run(app, host=\"0.0.0.0\", port=int(os.getenv(\"PORT\", 8000)), log_level=\"info\")'"]
