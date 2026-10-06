from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.dataset_registry_routes import router as dataset_registry_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.api.agent_routes import router as agent_router


app = FastAPI(
    title="DataGuard API",
    description="Agentic System for Automated ETL Pipeline Auditing and Anomaly Detection",
    version="2.0.0",
)

# ---------------------------------------------------------
# Configure Cross-Origin Resource Sharing (CORS)
# ---------------------------------------------------------
cors_origins_env = os.getenv("CORS_ORIGINS")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://dataguard-pink.vercel.app",
]
if cors_origins_env:
    for o in cors_origins_env.split(","):
        trimmed = o.strip()
        if trimmed and trimmed not in allowed_origins:
            allowed_origins.append(trimmed)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Ensure reports directory exists
# ---------------------------------------------------------
os.makedirs("reports", exist_ok=True)

# ---------------------------------------------------------
# Register API Routes
# ---------------------------------------------------------
app.include_router(auth_router)
app.include_router(dataset_registry_router)
app.include_router(audit_router)
app.include_router(agent_router)


# ---------------------------------------------------------
# ML Detection Proof Endpoint (Direct conceptual URL)
# ---------------------------------------------------------
from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.ml_proof import MLDetectionProofResponse
from app.services.ml_proof_service import MLProofService

@app.get("/audits/{inspection_id}/ml-proof", response_model=MLDetectionProofResponse)
def get_ml_proof_direct(
    inspection_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Direct endpoint for transparent ML detection proof as specified in DataGuard 2.0 viva contract.
    """
    try:
        return MLProofService.get_ml_proof_response(db, inspection_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------
@app.get("/health")
def health_check():
    """
    Minimal health check endpoint for production uptime monitors & cloud platforms.
    """
    return {
        "status": "healthy",
        "service": "DataGuard API",
        "version": "2.0.0",
    }


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "project": "DataGuard 2.0",
        "description": "Agentic System for Automated ETL Pipeline Auditing and Anomaly Detection",
        "status": "Backend is running successfully",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "auth": "/auth",
            "datasets": "/datasets",
            "audit": "/audit",
            "agents": "/agents",
        },
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)