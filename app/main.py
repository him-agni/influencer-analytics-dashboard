"""
FastAPI application entry point.
Configures lifespan, CORS, scheduler, and static file serving.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import logger
from app.database import create_tables
from app.api.v1.router import router as v1_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ───────────────────────────────────────────
    logger.info("Starting Influencer Analytics Dashboard")

    # Create database tables
    logger.info("Creating database tables...")
    # Import models so they register with Base
    import app.models  # noqa: F401
    await create_tables()
    logger.info("Database tables ready")

    # Start scheduler if enabled
    scheduler = None
    if settings.scheduler_enabled:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from app.scheduler.jobs import refresh_all_profiles

            scheduler = AsyncIOScheduler()
            scheduler.add_job(
                refresh_all_profiles,
                "interval",
                hours=settings.scheduler_interval_hours,
                id="refresh_profiles",
                name="Refresh all profiles",
            )
            scheduler.start()
            logger.info(
                f"Scheduler started (interval: {settings.scheduler_interval_hours}h)"
            )
        except Exception as e:
            logger.warning(f"Scheduler failed to start: {e}")

    yield

    # ── Shutdown ──────────────────────────────────────────
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    logger.info("Application shutdown complete")


# ── App Factory ───────────────────────────────────────────────

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="YouTube Influencer Analytics Dashboard — Collect, analyze, and visualize channel performance data.",
    lifespan=lifespan,
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(v1_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "scheduler_enabled": settings.scheduler_enabled,
        "sentiment_enabled": settings.sentiment_enabled,
        "youtube_configured": bool(settings.youtube_api_key),
    }


# Serve static frontend files (MUST be last — catches all unmatched routes)
static_dir = Path(__file__).parent.parent / "frontend"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
