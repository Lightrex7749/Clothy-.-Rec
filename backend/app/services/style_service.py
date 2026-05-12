"""
ClothyRec – Item styling service.

Orchestrates the full pipeline:
  guardrail → classify → direction → FAISS search →
  occasion re-rank → colour harmony → skin re-rank → response

V2: Uses search_with_dedup for improved retrieval quality,
    adds similarity scores and source domain to recommendations.
"""

from __future__ import annotations

import logging
import numpy as np
from PIL import Image
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.config import get_settings
from app.ml.singleton import get_registry
from app.ml.classifiers import classify_both
from app.ml.faiss_index import search_index, search_with_dedup
from app.services.scoring import (
    clothing_color_stats,
    color_harmony_score,
    skin_match_score,
    occasion_text_embeddings,
)

logger = logging.getLogger("clothyrec.style")


def process_item(
    image: Image.Image,
    occasion_text: str = "",
    mode: str = "catalog",
    use_skin: bool = False,
    skin_profile: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Full item-styling pipeline.

    Returns a dict matching the API response schema.
    """
    cfg = get_settings()
    reg = get_registry()

    # ── 1. CLIP embed the query image ──────────────────────────────────
    query_vec = reg.clip.embed_image(image)

    # ── 2. Clothing guardrail ──────────────────────────────────────────
    ok, cloth_score, non_score = reg.guardrail.check(query_vec)
    clothing_check = {
        "ok": ok,
        "clothing_score": cloth_score,
        "nonclothing_score": non_score,
    }
    if not ok:
        return {
            "clothing_check": clothing_check,
            "predictions": None,
            "direction": None,
            "recommendations": [],
            "explanation": (
                "This image doesn't appear to be a clothing item. "
                "Please upload a clear photo of a garment (shirt, pants, etc.)."
            ),
        }

    # ── 3. Classify with both models ───────────────────────────────────
    resnet_pred, effnet_pred, ensemble_pred = classify_both(
        image, reg.resnet, reg.effnet, reg.id2label, reg.device
    )
    predictions = {
        "resnet": resnet_pred,
        "effnet": effnet_pred,
        "ensemble": ensemble_pred,
    }

    # ── 4. Confidence threshold ────────────────────────────────────────
    if ensemble_pred["confidence"] < cfg.MIN_CLASSIFIER_CONF:
        return {
            "clothing_check": clothing_check,
            "predictions": predictions,
            "direction": None,
            "recommendations": [],
            "explanation": (
                f"Low classifier confidence ({ensemble_pred['confidence']:.0%}). "
                "Try uploading a clearer, well-lit photo of the garment."
            ),
        }

    # ── 5. Determine direction ─────────────────────────────────────────
    pred_label = ensemble_pred["label"]
    if pred_label in cfg.TOP_CLASSES:
        direction = "top->bottom"
        search_idx = reg.index_bottoms
        search_meta = reg.bottoms_meta_idx
        occasion_dir = "bottoms"
        is_top_query = True
    elif pred_label in cfg.BOTTOM_CLASSES:
        direction = "bottom->top"
        search_idx = reg.index_tops
        search_meta = reg.tops_meta_idx
        occasion_dir = "tops"
        is_top_query = False
    else:
        return {
            "clothing_check": clothing_check,
            "predictions": predictions,
            "direction": None,
            "recommendations": [],
            "explanation": f"Predicted class '{pred_label}' is not mapped to top or bottom.",
        }

    # ── 6. FAISS search (V2: with dedup + threshold) ───────────────────
    if reg.v2_mode:
        img_scores, meta_rows = search_with_dedup(
            search_idx, query_vec, search_meta,
            reg.embeddings_all,
            k=cfg.FAISS_SEARCH_K,
            sim_threshold=cfg.SIMILARITY_THRESHOLD,
            dedup_threshold=cfg.DUPLICATE_THRESHOLD,
        )
    else:
        img_scores, meta_rows = search_index(
            search_idx, query_vec, search_meta, k=cfg.FAISS_SEARCH_K
        )

    # ── 7. Occasion text scoring ───────────────────────────────────────
    txt_vec = occasion_text_embeddings(reg.clip, occasion_text, occasion_dir)
    cand_emb = reg.embeddings_all[meta_rows]
    txt_scores = (cand_emb @ txt_vec.T).reshape(-1)

    # Hybrid score
    hybrid = cfg.W_IMG * img_scores + cfg.W_TXT * txt_scores

    # ── 8. Colour harmony + skin re-ranking ────────────────────────────
    query_hsv = clothing_color_stats(image)
    undertone = "neutral"
    if use_skin and skin_profile:
        undertone = skin_profile.get("undertone", "neutral")

    recs: List[Dict[str, Any]] = []
    for i in range(len(meta_rows)):
        row_idx = int(meta_rows[i])
        row = reg.meta.iloc[row_idx]
        label = row.get("label", "unknown")

        # Skip rows with no label
        if not label or str(label) == "nan":
            continue

        img_path = row.get("path", "")
        source = row.get("source", "legacy")

        # Compute item HSV from stored path (if image exists, else skip)
        path_exists = bool(img_path) and Path(img_path).is_file()
        try:
            if path_exists:
                item_img = Image.open(img_path).convert("RGB")
                item_hsv = clothing_color_stats(item_img)
            else:
                raise FileNotFoundError(img_path)
        except Exception:
            item_hsv = (0.0, 0.0, 128.0)

        if is_top_query:
            harmony = color_harmony_score(query_hsv, item_hsv)
        else:
            harmony = color_harmony_score(item_hsv, query_hsv)

        skin = skin_match_score(item_hsv, undertone) if use_skin else 0.80

        final = (
            cfg.W_CLIP_HYBRID * float(hybrid[i])
            + cfg.W_HARMONY * harmony
            + cfg.W_SKIN * skin
        )

        # Build image URL
        rel_path = row.get("rel_path", "")
        image_url = row.get("image_url", "")

        # V2 metadata has image_url pre-computed; V1 uses rel_path
        if not image_url and rel_path and source == "legacy":
            image_url = f"/static/dataset/{rel_path}"

        if image_url and not path_exists:
            image_url = ""

        recs.append({
            "label": label,
            "score": round(final, 4),
            "similarity_score": round(float(img_scores[i]), 4),
            "img_score": round(float(img_scores[i]), 4),
            "txt_score": round(float(txt_scores[i]), 4),
            "harmony": round(harmony, 4),
            "skin": round(skin, 4),
            "image_path": img_path,
            "rel_path": rel_path,
            "image_url": image_url,
            "source": source,
        })

    # Sort by final score descending, take top k
    recs.sort(key=lambda r: r["score"], reverse=True)
    recs = recs[: cfg.REC_K]

    # ── 9. Generate explanation ────────────────────────────────────────
    top_labels = list({r["label"] for r in recs[:3]})
    explanation = (
        f"Your {pred_label.replace('_', ' ')} was identified with "
        f"{ensemble_pred['confidence']:.0%} confidence. "
        f"Showing {direction.replace('->', ' → ')} recommendations"
    )
    if occasion_text:
        explanation += f" for '{occasion_text}'"
    explanation += f". Top picks include {', '.join(top_labels)}."

    if reg.v2_mode and recs:
        # Add retrieval quality info
        avg_sim = np.mean([r["similarity_score"] for r in recs])
        sources = set(r["source"] for r in recs)
        explanation += f" (avg similarity: {avg_sim:.2f}, sources: {', '.join(sources)})"

    return {
        "clothing_check": clothing_check,
        "predictions": predictions,
        "direction": direction,
        "recommendations": recs,
        "explanation": explanation,
    }
