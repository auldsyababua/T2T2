"""
Minimal test to verify Railway deployment
"""
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "T2T2 Backend is running!", "port": os.environ.get("PORT", "unknown")}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))