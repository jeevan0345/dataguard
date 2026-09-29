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
]
if cors_origins_env:
    allowed_origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
            "docs": "/docs",
            "auth": "/auth",
            "datasets": "/datasets",
            "audit": "/audit",
            "agents": "/agents",
        },
    }