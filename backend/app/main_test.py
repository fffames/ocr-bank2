from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"status": "working", "message": "Deployment test successful"}

@app.get("/health")
async def health():
    return {"status": "healthy"}