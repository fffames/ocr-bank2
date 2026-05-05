from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import sys

print("🚀 Starting FastAPI app...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("✅ FastAPI app startup complete!")
    port = os.getenv("PORT", "unknown")
    print(f"🎯 Listening on port: {port}")
    yield
    # Shutdown
    print("👋 FastAPI app shutting down...")

app = FastAPI(title="Test API", lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "working",
        "message": "Deployment test successful",
        "python_version": sys.version,
        "env_port": os.getenv("PORT", "not set")
    }

@app.get("/health")
async def health():
    # Simple, fast healthcheck response
    return JSONResponse(
        content={"status": "healthy"},
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🎯 Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)