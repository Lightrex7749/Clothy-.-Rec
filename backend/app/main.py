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

# Mount dataset images if DATA_ROOT is set, or use repo fallback
dataset_dir = None
if cfg.DATA_ROOT:
    data_root = cfg.DATA_ROOT.replace("\\", "/")
    # If data_root points to parent of dataset_clean, adjust
    candidate = os.path.join(data_root, "dataset_clean")
    if os.path.isdir(candidate):
        dataset_dir = candidate
    elif os.path.isdir(data_root):
        dataset_dir = data_root
else:
    repo_candidate = cfg.BASE_DIR.parent / "data" / "dataset_clean"
    if repo_candidate.is_dir():
        dataset_dir = str(repo_candidate)

if dataset_dir:
    app.mount("/static/dataset", StaticFiles(directory=dataset_dir), name="dataset")
    logger.info("Serving dataset images from %s", dataset_dir)

# ── V2 static image directories ───────────────────────────────────────
v2_dir = cfg.get_v2_dir()

# Ecommerce product images
v2_ecom_dir = v2_dir / "datasets" / "fashion_products" / "images"
if v2_ecom_dir.is_dir():
    app.mount("/static/v2/ecommerce", StaticFiles(directory=str(v2_ecom_dir)), name="v2_ecommerce")
    logger.info("Serving V2 ecommerce images from %s", v2_ecom_dir)

# DeepFashion inventory images
v2_df_dir = v2_dir / "datasets" / "deepfashion_subset"
if v2_df_dir.is_dir():
    app.mount("/static/v2/deepfashion", StaticFiles(directory=str(v2_df_dir)), name="v2_deepfashion")
    logger.info("Serving V2 DeepFashion images from %s", v2_df_dir)
else:
    legacy_df_dir = v2_dir / "deepfashion_inventory"
    if legacy_df_dir.is_dir():
        app.mount("/static/v2/deepfashion", StaticFiles(directory=str(legacy_df_dir)), name="v2_deepfashion")
        logger.info("Serving V2 DeepFashion images from legacy path %s", legacy_df_dir)

# Dataset clean images (ecommerce classified)
v2_clean_dir = v2_dir / "datasets" / "ecommerce" / "dataset_clean"
if v2_clean_dir.is_dir():
    app.mount("/static/v2/dataset_clean", StaticFiles(directory=str(v2_clean_dir)), name="v2_dataset_clean")
    logger.info("Serving V2 dataset_clean images from %s", v2_clean_dir)

# Prompt showcase images
v2_prompt_dir = v2_dir / "prompt_data"
if v2_prompt_dir.is_dir():
    app.mount("/static/prompts", StaticFiles(directory=str(v2_prompt_dir)), name="prompt_images")
    logger.info("Serving prompt showcase images from %s", v2_prompt_dir)

# ── Routes ─────────────────────────────────────────────────────────────
from app.routes.health import router as health_router
from app.routes.style import router as style_router
from app.routes.skin import router as skin_router
from app.routes.chat import router as chat_router
from app.routes.image_gen import router as image_gen_router
from app.routes.prompts import router as prompts_router

app.include_router(health_router)
app.include_router(style_router)
app.include_router(skin_router)
app.include_router(chat_router)
app.include_router(image_gen_router)
app.include_router(prompts_router)

@app.get("/")
async def root():
    return {"app": "ClothyRec", "version": "1.0.0", "status": "running"}
