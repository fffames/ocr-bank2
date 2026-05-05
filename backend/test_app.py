from fastapi import FastAPI

app = FastAPI(title="OCR Bank API")

@app.get("/")
async def root():
    return {"message": "OCR Bank API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)