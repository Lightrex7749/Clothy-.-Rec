"""
ClothyRec – Model registry (singleton).

Everything that is expensive to load (PyTorch models, CLIP, FAISS indices,
metadata, YOLO, MTCNN) is instantiated **once** here and then injected
into services via FastAPI's lifespan / dependency system.

V2: Loads ConvNeXt-Tiny, combined FAISS index (57,672 vectors),
    and mixed-domain metadata (ecommerce + DeepFashion).
"""

from __future__ import annotations

import json
import logging
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional

from app.config import get_settings
from app.ml.classifiers import load_convnext_tiny, load_resnet18, load_effnet_b0
from app.ml.clip_engine import CLIPEngine
from app.ml.faiss_index import load_master_index, build_subset_index
from app.ml.guardrails import ClothingGuardrail
from app.services.path_repair import repair_paths, repair_v2_paths, derive_v2_labels

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

    # V2 flag
    v2_mode: bool = False


# ── Global instance ────────────────────────────────────────────────────
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Return the global registry.  Must call `initialise_registry()` first."""
    if _registry is None:
        raise RuntimeError("ModelRegistry not initialised – call initialise_registry() first")
    return _registry


def _try_v2_init(cfg, device) -> Optional[ModelRegistry]:
    """Attempt to load V2 assets. Returns None if V2 files not found."""
    v2_dir = cfg.get_v2_dir()

    # Check for V2 assets
    combined_meta_path = v2_dir / "deepfashion_inventory" / "combined_metadata.csv"
    combined_emb_path = v2_dir / "deepfashion_inventory" / "combined_embeddings.npy"
    combined_idx_path = v2_dir / "deepfashion_inventory" / "combined_faiss.index"
    convnext_path = v2_dir / "models" / "checkpoints" / "best_convnext_tiny.pth"
    label_maps_dir = v2_dir / "models" / "label_maps"

    required = [combined_meta_path, combined_emb_path, combined_idx_path, convnext_path]
    missing = [p for p in required if not p.exists()]
    if missing:
        logger.warning("V2 assets not found: %s – falling back to V1", [str(m) for m in missing])
        return None

    logger.info("=== Loading V2 assets from %s ===", v2_dir)

    # ── 1. Load metadata, derive labels, repair paths ──────────────────
    meta = pd.read_csv(combined_meta_path)
    meta = derive_v2_labels(meta)
    meta = repair_v2_paths(meta, v2_dir, base_dir=cfg.BASE_DIR)

    # Drop rows with no usable label (non-clothing items)
    labelled_count = meta["label"].notna().sum()
    total = len(meta)
    logger.info("V2 metadata: %d total rows, %d with labels (%.0f%%)",
                total, labelled_count, 100 * labelled_count / total)

    # ── 2. Load embeddings + FAISS index ───────────────────────────────
    embeddings = np.load(str(combined_emb_path))
    master_idx = load_master_index(combined_idx_path)
    logger.info("Loaded V2 index: %d vectors (%dd), %d meta rows",
                master_idx.ntotal, embeddings.shape[1], len(meta))

    # ── 3. Load V2 label maps ─────────────────────────────────────────
    idx_to_class_path = label_maps_dir / "idx_to_class.json"
    class_to_idx_path = label_maps_dir / "class_to_idx.json"

    with open(idx_to_class_path) as f:
        raw_id2label = json.load(f)
    with open(class_to_idx_path) as f:
        label2id = json.load(f)

    # idx_to_class keys are strings ("0", "1", ...)
    id2label = {int(k): v for k, v in raw_id2label.items()}
    num_classes = len(id2label)
    label_list = [id2label[i] for i in range(num_classes)]
    logger.info("V2 classes (%d): %s", num_classes, label_list)

    # ── 4. Build top / bottom sub-indices ──────────────────────────────
    idx_tops, tops_meta = build_subset_index(embeddings, meta, cfg.TOP_CLASSES)
    idx_bots, bots_meta = build_subset_index(embeddings, meta, cfg.BOTTOM_CLASSES)
    logger.info("V2 sub-indices: tops=%d, bottoms=%d", idx_tops.ntotal, idx_bots.ntotal)

    # ── 5. Load ConvNeXt-Tiny classifier ───────────────────────────────
    convnext = load_convnext_tiny(num_classes, convnext_path, device)
    logger.info("Loaded ConvNeXt-Tiny (V2) with %d classes", num_classes)

    # ── 6. Load CLIP ───────────────────────────────────────────────────
    clip = CLIPEngine(device=device)
    logger.info("Loaded CLIP ViT-B/32")

    # ── 7. Build guardrail ─────────────────────────────────────────────
    guardrail = ClothingGuardrail(clip, margin=cfg.CLOTHING_MARGIN)
    logger.info("Clothing guardrail ready")

    # ── Assemble registry ──────────────────────────────────────────────
    return ModelRegistry(
        resnet=convnext,          # Both slots point to ConvNeXt (V2 mode)
        effnet=convnext,          # classify_both detects this and uses temperature perturbation
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
        v2_mode=True,
    )


def initialise_registry() -> ModelRegistry:
    """Load all models, indices, and metadata.  Called once at app startup."""
    global _registry
    if _registry is not None:
        return _registry

    cfg = get_settings()
    device = cfg.DEVICE
    logger.info("Initialising model registry on device=%s", device)

    # ── Try V2 first ───────────────────────────────────────────────────
    v2_reg = _try_v2_init(cfg, device)
    if v2_reg is not None:
        _registry = v2_reg
        logger.info("Model registry initialised successfully (V2 mode) ✓")
        return _registry

    # ── V1 fallback ────────────────────────────────────────────────────
    logger.info("Loading V1 assets (legacy path)")

    # ── 1. Load metadata & embeddings ──────────────────────────────────
    index_dir = cfg.get_index_dir()
    meta = pd.read_csv(index_dir / "meta.csv")
    embeddings = np.load(index_dir / "clip_emb.npy")
    master_idx = load_master_index(index_dir / "clip_faiss.index")
    logger.info("Loaded index: %d vectors, %d meta rows", master_idx.ntotal, len(meta))

    # Path repair
    meta = repair_paths(meta, cfg.DATA_ROOT, base_dir=cfg.BASE_DIR)

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
        v2_mode=False,
    )
    logger.info("Model registry initialised successfully (V1 mode) ✓")
    return _registry
