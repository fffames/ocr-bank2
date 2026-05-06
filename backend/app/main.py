from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and startup."""
    print("🚀 Starting OCR Bank API...")

    # Startup
    try:
        # Create image storage directory
        os.makedirs(settings.image_storage_path, exist_ok=True)

        # Create ChromaDB directory
        os.makedirs(settings.chromadb_persist_directory, exist_ok=True)

        # Create uploads directory
        os.makedirs("uploads", exist_ok=True)

        print("✅ Directories created successfully")
        print(f"   - Images: {settings.image_storage_path}")
        print(f"   - ChromaDB: {settings.chromadb_persist_directory}")
        print(f"   - Uploads: uploads")

        # Mount static files AFTER directories are created
        try:
            # Mount the full image path so /tmp/ocr_images/file.jpg works
            app.mount("/tmp/ocr_images", StaticFiles(directory=settings.image_storage_path), name="images")
            print(f"  ✅ Image serving mounted at /tmp/ocr_images -> {settings.image_storage_path}")
        except Exception as e:
            print(f"  ⚠️  Could not mount image serving: {e}")

    except Exception as e:
        print(f"⚠️  Warning: Error creating directories: {e}")

    print("✅ OCR Bank API startup complete!")

    yield

    # Shutdown
    print("👋 OCR Bank API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="OCR Bank API",
    description="Bank receipt OCR and RAG chatbot API",
    version="1.0.0",
    lifespan=lifespan
)

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

# Configure CORS from environment variable
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

# Health check endpoint - CRITICAL FOR RAILWAY
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import routers with better error handling
print("📦 Loading API routers...")
try:
    from app.api import auth, admin, upload, receipts, chat, templates, user_settings, export, income, income_categories, salary, ocr_corrections

    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    print("  ✅ Authentication router loaded")

    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    print("  ✅ Admin router loaded")

    # Load all routers (database is now properly configured)
    app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
    app.include_router(receipts.router, prefix="/api/receipts", tags=["receipts"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(templates.router, prefix="/api", tags=["templates"])
    app.include_router(user_settings.router, prefix="/api/user", tags=["user_settings"])
    app.include_router(export.router, prefix="/api/export", tags=["export"])
    app.include_router(income.router, prefix="/api/income", tags=["income"])
    app.include_router(income_categories.router, prefix="/api/income-categories", tags=["income_categories"])
    app.include_router(salary.router, prefix="/api/salary", tags=["salary"])
    app.include_router(ocr_corrections.router, prefix="/api", tags=["ocr_corrections"])
    print("  ✅ All database routers loaded")

    print("✅ All routers loaded successfully")
    # Note: Static file serving is now mounted in lifespan() after directory creation

except Exception as e:
    import traceback
    print(f"⚠️  Warning: Router import error: {e}")
    print(f"⚠️  Traceback: {traceback.format_exc()}")
    print("⚠️  App will start with limited functionality")
