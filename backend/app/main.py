from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.routes import (
    health,
    users,
    auth,
    profiles,
    trust,
    safety,
    privacy,
    reports,
    blocks,
    alerts,
    dashboard,
    connections,
)


# Create all tables on startup (V1 — Alembic migrations in later versions)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TrustMatch AI API",
    description="Backend API for TrustMatch AI — connecting people with confidence.",
    version="1.0.0",
)

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(connections.router)
app.include_router(trust.router)
app.include_router(safety.router)
app.include_router(privacy.router)
app.include_router(reports.router)
app.include_router(blocks.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)


@app.get("/", tags=["root"])
def root():
    return {"message": "TrustMatch AI API v1 — visit /docs for Swagger UI"}

