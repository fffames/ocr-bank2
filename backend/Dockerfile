FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PaddleOCR and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
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

# Run the proper main app
CMD ["python", "-u", "-c", "import sys; import traceback; from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')"]
