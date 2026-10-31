from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    allow_origin_regex=r"https?://.*",
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


FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="frontend-assets")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_spa(full_path: str):
    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        candidate = (FRONTEND_DIST_DIR / full_path).resolve()
        if full_path and candidate.is_file() and str(candidate).startswith(str(FRONTEND_DIST_DIR.resolve())):
            return FileResponse(str(candidate))
        return FileResponse(str(index_file))
    return {
        "application": settings.APP_NAME,
        "status": "running",
        "frontend_dev_url": "http://localhost:5173",
        "api_docs_url": "http://127.0.0.1:8000/docs",
    }

