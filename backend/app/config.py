"""
ClothyRec – centralised configuration.

All tunables live here so nothing is scattered across modules.
Reads from environment / .env via pydantic-settings.
"""

import os
import torch
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings – override via env vars or .env file."""

    # ── Paths ──────────────────────────────────────────────────────────
    # Root of this backend package (backend/)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Where the dataset_clean/ folder lives on this machine.
    # e.g. C:/Users/HP/.cache/kagglehub/.../dataset_clean
    DATA_ROOT: str = ""

    # Model & index asset directories
    MODELS_DIR: str = ""   # defaults to BASE_DIR/../models
    INDEX_DIR: str = ""    # defaults to BASE_DIR/../clip_index/fashion_reco_index

    # Upload directory for saved images / crops
    UPLOAD_DIR: str = ""   # defaults to BASE_DIR/static/uploads

    # ── Device ─────────────────────────────────────────────────────────
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

    # ── Class mappings ─────────────────────────────────────────────────
    TOP_CLASSES: set[str] = {
        "casual_shirts",
        "formal_shirts",
        "printed_tshirts",
        "solid_tshirts",
        "printed_hoodies",
    }
    BOTTOM_CLASSES: set[str] = {
        "jeans",
        "formal_pants",
        "men_cargos",
    }

    # ── Scoring weights ────────────────────────────────────────────────
    W_IMG: float = 0.70          # image-to-image similarity weight
    W_TXT: float = 0.30          # occasion text weight
    W_CLIP_HYBRID: float = 0.65  # hybrid CLIP in final score
    W_HARMONY: float = 0.20      # color harmony in final score
    W_SKIN: float = 0.15         # skin match in final score

    # ── Thresholds ─────────────────────────────────────────────────────
    CLOTHING_MARGIN: float = 0.03        # CLIP clothing vs non-clothing margin
    MIN_CLASSIFIER_CONF: float = 0.40    # ensemble confidence floor
    FAISS_SEARCH_K: int = 150            # how many candidates to pull from FAISS
    REC_K: int = 8                       # final recommendations returned

    # ── CORS ───────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"

    # ── Optional Gemini (server-side only, for explanations) ───────────
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # ── Computed defaults ──────────────────────────────────────────────
    def get_models_dir(self) -> Path:
        if self.MODELS_DIR:
            return Path(self.MODELS_DIR)
        return self.BASE_DIR.parent / "models"

    def get_index_dir(self) -> Path:
        if self.INDEX_DIR:
            return Path(self.INDEX_DIR)
        return self.BASE_DIR.parent / "clip_index" / "fashion_reco_index"

    def get_upload_dir(self) -> Path:
        if self.UPLOAD_DIR:
            p = Path(self.UPLOAD_DIR)
        else:
            p = self.BASE_DIR / "static" / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache()
def get_settings() -> Settings:
    return Settings()
