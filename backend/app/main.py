from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models import Base
from app.services.seeder import seed_initial_data
from app.api.routes import (
    auth,
    dashboard,
    datasets,
    analysis,
    predictions,
    locations,
    risk,
    comparison,
    insights,
    reports,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "NAGARNEXUS – AI-Powered Hyperlocal Urban Intelligence and Prediction Platform. "
        "Turning Urban Data Into Intelligent Decisions."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(predictions.router)
app.include_router(locations.router)
app.include_router(risk.router)
app.include_router(comparison.router)
app.include_router(insights.router)
app.include_router(reports.router)


@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": "Turning Urban Data Into Intelligent Decisions.",
    }

