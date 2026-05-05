from fastapi import FastAPI
import os
import sys

print("🚀 Starting FastAPI app...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

app = FastAPI(title="Test API")

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
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🎯 Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)