"""
ClothyRec – Scoring functions.

Covers:
  • Color harmony scoring (HSV-based)
  • Skin-undertone compatibility scoring
  • Occasion text scoring via CLIP templates
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional

from app.ml.clip_engine import CLIPEngine


# ═══════════════════════════════════════════════════════════════════════
# 1. Clothing colour statistics (HSV)
# ═══════════════════════════════════════════════════════════════════════

def clothing_color_stats(img: Image.Image | np.ndarray, resize: int = 180) -> Tuple[float, float, float]:
    """
    Compute mean H, S, V on non-background pixels.

    Returns (H_mean, S_mean, V_mean) where H ∈ [0,180], S/V ∈ [0,255].
    """
    if isinstance(img, Image.Image):
        arr = np.array(img.convert("RGB"))
    else:
        arr = img
        if arr.shape[2] == 4:  # RGBA
            arr = arr[:, :, :3]

    h, w = arr.shape[:2]
    scale = resize / max(h, w)
    arr = cv2.resize(arr, (int(w * scale), int(h * scale)))

    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    # Mask out likely background (very low saturation or very bright white)
    mask = (S > 35) & (V < 245)
    if mask.sum() < 200:
        mask = np.ones_like(S, dtype=bool)

    return float(H[mask].mean()), float(S[mask].mean()), float(V[mask].mean())


# ═══════════════════════════════════════════════════════════════════════
# 2. Colour harmony score
# ═══════════════════════════════════════════════════════════════════════

def _hue_dist(h1: float, h2: float) -> float:
    d = abs(h1 - h2)
    return min(d, 180 - d)


def color_harmony_score(top_stats: Tuple, bottom_stats: Tuple) -> float:
    """
    Heuristic colour harmony between a top and a bottom item.

    Considers:
      - neutral bonus (low saturation bottoms pair well with colorful tops)
      - brightness contrast
      - hue distance penalty
    """
    ht, st, vt = top_stats
    hb, sb, vb = bottom_stats

    neutral_bonus = 1.0 - min(sb / 255.0, 1.0)
    if st > 90:  # colourful top → prefer neutral bottoms more
        neutral_bonus *= 1.3

    v_contrast = min(abs(vt - vb) / 255.0, 1.0)
    hue_penalty = (_hue_dist(ht, hb) / 90.0) * (sb / 255.0)

    score = 0.55 * neutral_bonus + 0.35 * v_contrast - 0.20 * hue_penalty
    return round(float(np.clip(score, 0.0, 1.0)), 4)


# ═══════════════════════════════════════════════════════════════════════
# 3. Skin-undertone compatibility
# ═══════════════════════════════════════════════════════════════════════

def _color_family_from_hsv(h: float, s: float, _v: float) -> str:
    if s < 45:
        return "neutral"
    if (h <= 35) or (h >= 160) or (35 < h <= 80):
        return "warm"
    return "cool"


def skin_match_score(item_hsv: Tuple, undertone: str) -> float:
    """
    Score how well an item's colour family matches a skin undertone.

    - Neutral colours score high for everyone.
    - Matching undertone → highest.
    - Clashing undertone → low.
    """
    h, s, v = item_hsv
    fam = _color_family_from_hsv(h, s, v)
    if fam == "neutral":
        return 0.95
    if undertone == "neutral":
        return 0.80
    return 1.00 if fam == undertone else 0.45


# ═══════════════════════════════════════════════════════════════════════
# 4. Occasion text scoring
# ═══════════════════════════════════════════════════════════════════════

def occasion_text_embeddings(
    clip: CLIPEngine,
    occasion_text: str,
    direction: str,
) -> np.ndarray:
    """
    Build mean CLIP text embedding for occasion scoring.

    Parameters
    ----------
    direction : "tops" or "bottoms" — controls prompt templates
    """
    occasion_text = (occasion_text or "").strip() or "casual everyday"

    if direction == "bottoms":
        templates = [
            f"men's {occasion_text} outfit pants",
            f"men's {occasion_text} trousers",
            f"men's {occasion_text} jeans outfit",
        ]
    else:  # tops
        templates = [
            f"men's {occasion_text} shirt",
            f"men's {occasion_text} t-shirt",
            f"men's {occasion_text} hoodie",
        ]

    return clip.embed_texts_mean(templates)
