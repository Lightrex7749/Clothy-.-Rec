"""
ClothyRec – Guardrails (clothing-vs-non-clothing CLIP check).

Pre-computes mean text embeddings for "clothing" and "non-clothing" prompts
and exposes a simple `check_clothing(image_embedding)` function.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

from app.ml.clip_engine import CLIPEngine


CLOTHING_PROMPTS = [
    "a photo of clothing",
    "a photo of a shirt",
    "a photo of pants",
    "a fashion product photo",
    "a photo of men's clothing",
]

NONCLOTHING_PROMPTS = [
    "a photo of a car",
    "a photo of a dog",
    "a photo of food",
    "a photo of a building",
    "a random object photo",
]


class ClothingGuardrail:
    """Pre-baked clothing vs non-clothing CLIP classifier."""

    def __init__(self, clip: CLIPEngine, margin: float = 0.03):
        self.margin = margin
        self.cloth_vec = clip.embed_texts_mean(CLOTHING_PROMPTS)
        self.non_vec = clip.embed_texts_mean(NONCLOTHING_PROMPTS)

    def check(self, image_vec: np.ndarray) -> Tuple[bool, float, float]:
        """
        Parameters
        ----------
        image_vec : (1, 512) normalised embedding

        Returns
        -------
        ok              : True if it looks like clothing
        clothing_score  : CLIP similarity to clothing prompts
        non_score       : CLIP similarity to non-clothing prompts
        """
        clothing_score = float((image_vec @ self.cloth_vec.T).flatten()[0])
        non_score = float((image_vec @ self.non_vec.T).flatten()[0])
        ok = clothing_score > (non_score + self.margin)
        return ok, round(clothing_score, 4), round(non_score, 4)
