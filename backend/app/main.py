"""
ClothyRec – FastAPI application entry point.

Loads all ML models at startup via the lifespan context manager,
mounts static file serving, and registers all API routes.
"""
from __future__ import annotations
import logging, os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.ml.singleton import initialise_registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("clothyrec")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all models once at startup."""
    logger.info("ClothyRec starting up …")
    initialise_registry()
    yield
    logger.info("ClothyRec shutting down.")


app = FastAPI(title="ClothyRec", version="1.0.0", lifespan=lifespan)

# ── CORS ───────────────────────────────────────────────────────────────
cfg = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ───────────────────────────────────────────────────────
upload_dir = cfg.get_upload_dir()
app.mount("/static/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Mount dataset images if DATA_ROOT is set
if cfg.DATA_ROOT:
    data_root = cfg.DATA_ROOT.replace("\\", "/")
    # If data_root points to parent of dataset_clean, adjust
    candidate = os.path.join(data_root, "dataset_clean")
    if os.path.isdir(candidate):
        dataset_dir = candidate
    elif os.path.isdir(data_root):
        dataset_dir = data_root
    else:
        dataset_dir = None

    if dataset_dir:
        app.mount("/static/dataset", StaticFiles(directory=dataset_dir), name="dataset")
        logger.info("Serving dataset images from %s", dataset_dir)

# ── Routes ─────────────────────────────────────────────────────────────
from app.routes.health import router as health_router
from app.routes.style import router as style_router
from app.routes.skin import router as skin_router
from app.routes.chat import router as chat_router

app.include_router(health_router)
app.include_router(style_router)
app.include_router(skin_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"app": "ClothyRec", "version": "1.0.0", "status": "running"}
