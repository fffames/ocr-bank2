FROM python:3.11-slim

WORKDIR /app

# No system dependencies needed - pure Python FastAPI app

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

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]