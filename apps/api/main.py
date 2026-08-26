from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.database import init_db
from apps.api.routers import (
    audit,
    communication,
    dashboard,
    demo,
    evaluation,
    payments,
    promises,
    recovery,
    review,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas on startup
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "RecoverX — Confidence-Gated AI Revenue Recovery Agent API.\n\n"
        "Core Philosophy: Detect -> Diagnose -> Calibrate Confidence -> Gate Autonomy -> "
        "Communicate -> Recover -> Verify -> Follow Up -> Measure.\n\n"
        "AI reasoning != Financial Authorization. Confidence != Permission. "
        "Deterministic Policy Engine retains final control."
    ),
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(dashboard.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(recovery.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(promises.router, prefix="/api")
app.include_router(communication.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(demo.router, prefix="/api")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RecoverX API",
        "environment": "synthetic-demo",
        "version": settings.app_version,
        "safeguards": "Deterministic Policy Engine Active",
    }
