from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import settings
import os

# Create FastAPI app
app = FastAPI(
    title="OCR Bank API",
    description="Bank receipt OCR and RAG chatbot API",
    version="1.0.0"
)

# Startup event - create necessary directories
@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup."""
    # Create image storage directory
    os.makedirs(settings.image_storage_path, exist_ok=True)

    # Create ChromaDB directory
    os.makedirs(settings.chromadb_persist_directory, exist_ok=True)

    # Create config directory for Google Sheets credentials
    config_dir = os.path.dirname(settings.google_sheets_credentials_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

    print(f"✅ Directories created:")
    print(f"   - Images: {settings.image_storage_path}")
    print(f"   - ChromaDB: {settings.chromadb_persist_directory}")
    print(f"   - Config: {config_dir}")

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed messages."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    error_detail = "; ".join(errors)
    return JSONResponse(
        status_code=422,
        content={"detail": error_detail}
    )

from fastapi.staticfiles import StaticFiles

# Mount static files for images
# In production (Railway), images are stored in /data/images
# In development, they're in ./backend/images
app.mount("/images", StaticFiles(directory=settings.image_storage_path), name="images")

# Configure CORS from environment variable
# Default to localhost for development
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["http://localhost:5173", "http://localhost:3000"]

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


# Import routers
from app.api import upload, receipts, chat, templates, user_settings, export

app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(receipts.router, prefix="/api/receipts", tags=["receipts"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(templates.router, prefix="/api", tags=["templates"])
app.include_router(user_settings.router, prefix="/api/user", tags=["user_settings"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
# app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
