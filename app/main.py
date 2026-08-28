"""
app/main.py
────────────
FastAPI application entry point.
Mounts static files and all API routers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.session import create_tables
from app.routes.evaluation_routes import router as eval_router
from app.routes.upload_routes import router as upload_router
from app.routes.voice_routes import router as voice_router
from app.utils.logging_config import get_logger, setup_logging

settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("startup", env="production")
    await create_tables()
    settings.ensure_dirs()
    yield
    logger.info("shutdown")


app = FastAPI(
    title="AI Multi-Agent Candidate Evaluation System",
    description=(
        "Evaluates candidates using 4 independent AI personas (Technical, HR, "
        "Hiring Manager, Skeptic), a structured multi-agent debate, and an "
        "evidence-based Judge agent for the final recommendation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (allow all for local development)
# NOTE: allow_credentials=True cannot be combined with a literal "*" origin per the
# CORS spec — browsers will reject credentialed responses. Since the frontend is
# served same-origin (via the StaticFiles mount below), CORS headers aren't needed
# for it at all. If you split the frontend out to its own origin later, set
# allow_credentials=False here or list explicit origins instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(upload_router)
app.include_router(eval_router)
app.include_router(voice_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "candidate-eval"}


# Serve static frontend.
# IMPORTANT: this mount must be registered LAST. Starlette matches routes in the
# order they were added, and a Mount("/") matches any path as a prefix — so if it
# were registered before /health (or any other route), it would swallow that
# request before FastAPI ever reached the real handler.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
