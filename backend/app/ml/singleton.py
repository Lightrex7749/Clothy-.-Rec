"""
ClothyRec – Model registry (singleton).

Everything that is expensive to load (PyTorch models, CLIP, FAISS indices,
metadata, YOLO, MTCNN) is instantiated **once** here and then injected
into services via FastAPI's lifespan / dependency system.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional

from app.config import get_settings
from app.ml.classifiers import load_resnet18, load_effnet_b0
from app.ml.clip_engine import CLIPEngine
from app.ml.faiss_index import load_master_index, build_subset_index
from app.ml.guardrails import ClothingGuardrail
from app.services.path_repair import repair_paths

logger = logging.getLogger("clothyrec.registry")


@dataclass
class ModelRegistry:
    """Holds every loaded model and data artefact for the lifetime of the process."""

    # Classifiers
    resnet: torch.nn.Module = None           # type: ignore[assignment]
    effnet: torch.nn.Module = None           # type: ignore[assignment]

    # Label maps
    label_list: list[str] = field(default_factory=list)
    label2id: Dict[str, int] = field(default_factory=dict)
    id2label: Dict[int, str] = field(default_factory=dict)
    num_classes: int = 0

    # CLIP
    clip: Optional[CLIPEngine] = None

    # FAISS
    master_index: object = None
    embeddings_all: Optional[np.ndarray] = None
    meta: Optional[pd.DataFrame] = None

    # Sub-indices (top / bottom)
    index_tops: object = None
    tops_meta_idx: Optional[np.ndarray] = None
    index_bottoms: object = None
    bottoms_meta_idx: Optional[np.ndarray] = None

    # Guardrails
    guardrail: Optional[ClothingGuardrail] = None

    # Device
    device: str = "cpu"


# ── Global instance ────────────────────────────────────────────────────
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Return the global registry.  Must call `initialise_registry()` first."""
    if _registry is None:
        raise RuntimeError("ModelRegistry not initialised – call initialise_registry() first")
    return _registry


def initialise_registry() -> ModelRegistry:
    """Load all models, indices, and metadata.  Called once at app startup."""
    global _registry
    if _registry is not None:
        return _registry

    cfg = get_settings()
    device = cfg.DEVICE
    logger.info("Initialising model registry on device=%s", device)

    # ── 1. Load metadata & embeddings ──────────────────────────────────
    index_dir = cfg.get_index_dir()
    meta = pd.read_csv(index_dir / "meta.csv")
    embeddings = np.load(index_dir / "clip_emb.npy")
    master_idx = load_master_index(index_dir / "clip_faiss.index")
    logger.info("Loaded index: %d vectors, %d meta rows", master_idx.ntotal, len(meta))

    # Path repair
    meta = repair_paths(meta, cfg.DATA_ROOT)

    # Label mapping (sorted unique – matches training order)
    label_list = sorted(meta["label"].unique().tolist())
    label2id = {l: i for i, l in enumerate(label_list)}
    id2label = {i: l for l, i in label2id.items()}
    num_classes = len(label_list)
    logger.info("Classes (%d): %s", num_classes, label_list)

    # ── 2. Build top / bottom sub-indices ──────────────────────────────
    idx_tops, tops_meta = build_subset_index(embeddings, meta, cfg.TOP_CLASSES)
    idx_bots, bots_meta = build_subset_index(embeddings, meta, cfg.BOTTOM_CLASSES)
    logger.info("Sub-indices: tops=%d, bottoms=%d", idx_tops.ntotal, idx_bots.ntotal)

    # ── 3. Load classifiers ────────────────────────────────────────────
    models_dir = cfg.get_models_dir()
    resnet = load_resnet18(num_classes, models_dir / "resnet18_best.pt", device)
    effnet = load_effnet_b0(num_classes, models_dir / "effb0_best.pt", device)
    logger.info("Loaded ResNet18 + EfficientNet-B0")

    # ── 4. Load CLIP ───────────────────────────────────────────────────
    clip = CLIPEngine(device=device)
    logger.info("Loaded CLIP ViT-B/32")

    # ── 5. Build guardrail ─────────────────────────────────────────────
    guardrail = ClothingGuardrail(clip, margin=cfg.CLOTHING_MARGIN)
    logger.info("Clothing guardrail ready")

    # ── Assemble registry ──────────────────────────────────────────────
    _registry = ModelRegistry(
        resnet=resnet,
        effnet=effnet,
        label_list=label_list,
        label2id=label2id,
        id2label=id2label,
        num_classes=num_classes,
        clip=clip,
        master_index=master_idx,
        embeddings_all=embeddings,
        meta=meta,
        index_tops=idx_tops,
        tops_meta_idx=tops_meta,
        index_bottoms=idx_bots,
        bottoms_meta_idx=bots_meta,
        guardrail=guardrail,
        device=device,
    )
    logger.info("Model registry initialised successfully ✓")
    return _registry
