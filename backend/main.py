from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.evidence_router import evidence_router

app = FastAPI(
    title="LogLens Evidence Subsystem API",
    description="Member 3 - Evidence Integrity, Cryptographic Hash Chain, and Local Ledger Service",
    version="1.0.0"
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Member 3 evidence router
app.include_router(evidence_router)


@app.get("/")
def root():
    return {
        "project": "LogLens",
        "subsystem": "Member 3 - Evidence Integrity Subsystem",
        "status": "ONLINE",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
