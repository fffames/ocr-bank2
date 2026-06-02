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
default_origins = ["http://localhost:5173", "http://localhost:3000", "https://frontend-mauve-tau-82.vercel.app"]
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else default_origins

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

# Import routers with better error handling - load each independently
print("📦 Loading API routers...")

def include_router_with_fallback(router_module, router_name, **kwargs):
    """Try to include a router, logging error if it fails."""
    try:
        app.include_router(router_module.router, **kwargs)
        print(f"  ✅ {router_name} router loaded")
        return True
    except Exception as e:
        print(f"  ❌ {router_name} router failed: {e}")
        return False

# Track which routers loaded successfully
loaded_routers = []
failed_routers = []

# Load migrate router FIRST (doesn't depend on database)
try:
    from app.api import migrate
    if include_router_with_fallback(migrate, "Migration", prefix="/api", tags=["migration"]):
        loaded_routers.append("migrate")
    else:
        failed_routers.append("migrate")
except ImportError as e:
    print(f"  ❌ Migrate router import failed: {e}")
    failed_routers.append("migrate")

# Try to load each router independently
router_configs = [
    ("auth", "Authentication", {"prefix": "/api/auth", "tags": ["authentication"]}),
    ("admin", "Admin", {"prefix": "/api/admin", "tags": ["admin"]}),
    ("upload", "Upload", {"prefix": "/api/upload", "tags": ["upload"]}),
    ("receipts", "Receipts", {"prefix": "/api/receipts", "tags": ["receipts"]}),
    ("chat", "Chat", {"prefix": "/api/chat", "tags": ["chat"]}),
    ("templates", "Templates", {"prefix": "/api", "tags": ["templates"]}),
    ("user_settings", "User Settings", {"prefix": "/api/user", "tags": ["user_settings"]}),
    ("export", "Export", {"prefix": "/api/export", "tags": ["export"]}),
    ("income", "Income", {"prefix": "/api/income", "tags": ["income"]}),
    ("income_categories", "Income Categories", {"prefix": "/api/income-categories", "tags": ["income_categories"]}),
    ("salary", "Salary", {"prefix": "/api/salary", "tags": ["salary"]}),
    ("ocr_corrections", "OCR Corrections", {"prefix": "/api", "tags": ["ocr_corrections"]}),
    ("cleanup", "Cleanup", {"prefix": "/api/cleanup", "tags": ["cleanup"]}),
]

for module_name, display_name, config in router_configs:
    try:
        module = __import__(f"app.api.{module_name}", fromlist=[module_name])
        if include_router_with_fallback(module, display_name, **config):
            loaded_routers.append(module_name)
        else:
            failed_routers.append(module_name)
    except ImportError as e:
        print(f"  ❌ {display_name} import failed: {e}")
        failed_routers.append(module_name)

# Print summary
print(f"\n📊 Router Loading Summary:")
print(f"  ✅ Loaded: {len(loaded_routers)} routers")
if failed_routers:
    print(f"  ❌ Failed: {len(failed_routers)} routers ({', '.join(failed_routers)})")
    print(f"  💡 Tip: If database routers failed, run POST /api/migrate to setup database")

if not loaded_routers:
    print("  ⚠️  WARNING: No routers loaded! App will have very limited functionality.")
