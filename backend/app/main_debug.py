from fastapi import FastAPI

print("🚀 Starting minimal debug app...")

# Create the simplest possible FastAPI app
app = FastAPI(title="OCR Bank Debug")

@app.get("/health")
async def health():
    print("✅ Health check called")
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "OCR Bank API - Debug Version", "status": "running"}

print("✅ Debug app loaded successfully")
