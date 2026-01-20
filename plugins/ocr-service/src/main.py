"""OCR Service - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FlowForge OCR Service",
    description="Optical character recognition service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ocr-service",
        "version": "1.0.0",
    }


@app.post("/api/v1/ocr/extract")
async def extract_text():
    # TODO: Implement OCR extraction
    return {"success": True, "message": "OCR extraction endpoint - coming soon"}
