from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="OCR Bank API",
    description="Bank receipt OCR and RAG chatbot API",
    version="1.0.0"
)
from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="images"), name="images")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
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
from app.api import upload, receipts, chat

app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(receipts.router, prefix="/api/receipts", tags=["receipts"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
# app.include_router(export.router, prefix="/api/export", tags=["export"])
# app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
