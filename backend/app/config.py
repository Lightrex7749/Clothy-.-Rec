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

    # ── V2 asset directory ─────────────────────────────────────────────
    V2_DIR: str = ""       # defaults to BASE_DIR/../PersonalFashionStylistV2

    # ── Device ─────────────────────────────────────────────────────────
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

    # ── Class mappings (V2 unified label set) ──────────────────────────
    TOP_CLASSES: set[str] = {
        # V2 labels
        "shirt",
        "tshirt",
        "hoodie",
        "sweater",
        "jacket",
        # Legacy V1 labels (kept for compatibility)
        "casual_shirts",
        "formal_shirts",
        "printed_tshirts",
        "solid_tshirts",
        "printed_hoodies",
    }
    BOTTOM_CLASSES: set[str] = {
        # V2 labels
        "jeans",
        "pants",
        # Legacy V1 labels
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
    FAISS_SEARCH_K: int = 200            # how many candidates to pull from FAISS (increased for V2)
    REC_K: int = 8                       # final recommendations returned
    SIMILARITY_THRESHOLD: float = 0.15   # minimum cosine similarity to keep
    DUPLICATE_THRESHOLD: float = 0.98    # suppress results above this mutual similarity

    # ── CORS ───────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"

    # ── Optional Gemini (server-side only, for explanations) ───────────
    GEMINI_API_KEY: str = ""
    GEMINI_IMAGE_MODEL: str = ""  # model name for image generation

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # ── Computed defaults ──────────────────────────────────────────────
    def get_v2_dir(self) -> Path:
        if self.V2_DIR:
            return Path(self.V2_DIR)
        return self.BASE_DIR.parent / "PersonalFashionStylistV2"

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
