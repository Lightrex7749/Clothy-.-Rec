"""
ClothyRec – CLIP embedding engine.

Wraps open_clip ViT-B/32 (laion2b_s34b_b79k) for image and text embedding.
All returned vectors are L2-normalised float32 numpy arrays (1 × 512).
"""

from __future__ import annotations

import numpy as np
import torch
import open_clip
from PIL import Image
from typing import List


class CLIPEngine:
    """Singleton-friendly CLIP wrapper."""

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        self.model = self.model.to(device).eval()
        self.tokenizer = open_clip.get_tokenizer("ViT-B-32")

    @torch.no_grad()
    def embed_image(self, img: Image.Image) -> np.ndarray:
        """Embed a single PIL image → (1, 512) normalised float32."""
        x = self.preprocess(img.convert("RGB")).unsqueeze(0).to(self.device)
        f = self.model.encode_image(x)
        f = f / f.norm(dim=-1, keepdim=True)
        return f.cpu().numpy().astype("float32")

    @torch.no_grad()
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string → (1, 512) normalised float32."""
        tokens = self.tokenizer([text]).to(self.device)
        t = self.model.encode_text(tokens)
        t = t / t.norm(dim=-1, keepdim=True)
        return t.cpu().numpy().astype("float32")

    def embed_texts_mean(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts and return their mean (re-normalised) → (1, 512)."""
        vecs = np.vstack([self.embed_text(t) for t in texts])
        v = vecs.mean(axis=0, keepdims=True)
        v = v / np.linalg.norm(v, axis=1, keepdims=True)
        return v.astype("float32")
