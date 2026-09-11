import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.evidence_router import evidence_router
from api.server import api_router

app = FastAPI(
    title="LogLens - Multi-Agent Cybersecurity Log Analysis Platform",
    description="AI-Assisted Multi-Agent Log Analysis, Incident Investigation, and Tamper-Evident Blockchain Platform",
    version="2.0.0"
)

# Enable CORS for SOC frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Member 3 evidence router (preserves existing test contracts)
app.include_router(evidence_router)

# Mount LogLens Unified Platform API router
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "project": "LogLens",
        "subsystem": "AI-Assisted Multi-Agent Log Analysis & Security Platform",
        "status": "ONLINE",
        "docs_url": "/docs",
        "api_dashboard": "/api/dashboard",
        "supported_sources": ["HDFS", "Linux", "Apache", "Generic"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
