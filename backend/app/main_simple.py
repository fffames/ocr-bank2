from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import os

# Create FastAPI app
app = FastAPI(
    title="OCR Bank API",
    description="Bank receipt OCR and RAG chatbot API",
    version="1.0.0"
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup."""
    try:
        os.makedirs(settings.image_storage_path, exist_ok=True)
        os.makedirs(settings.chromadb_persist_directory, exist_ok=True)
        os.makedirs("uploads", exist_ok=True)
        print("✅ Directories created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Error creating directories: {e}")

# Configure CORS
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "OCR Bank API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import routers (will be added later if this works)
print("🚀 Starting OCR Bank API...")
print("✅ Basic endpoints loaded")