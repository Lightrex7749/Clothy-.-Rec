"""
ClothyRec – CNN classifier loading & inference.

Loads ConvNeXt-Tiny (V2) checkpoint and provides a single
`classify_both` helper that returns predictions from all three "heads"
(ResNet, EffNet, Ensemble) for frontend API compatibility.

Internally, both heads run the same ConvNeXt model with slight
temperature perturbation to simulate the original two-model ensemble.
"""

from __future__ import annotations

import json
import torch
import torch.nn as nn
import torchvision.transforms as T
import timm
from PIL import Image
from pathlib import Path
from typing import Dict, Any, Optional


# ── ImageNet normalisation (same as training) ──────────────────────────
EVAL_TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
])


def load_convnext_tiny(num_classes: int, ckpt_path: str | Path, device: str) -> nn.Module:
    """Build a ConvNeXt-Tiny via timm and load the V2 checkpoint."""
    model = timm.create_model("convnext_tiny", pretrained=False, num_classes=num_classes)
    ck = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    # Handle both raw state_dict and wrapped {"model": state_dict} formats
    state_dict = ck.get("model", ck) if isinstance(ck, dict) and "model" in ck else ck
    if isinstance(state_dict, dict) and not any(k.startswith("head") or k.startswith("stages") for k in state_dict):
        # It's a wrapped dict but not a state_dict itself
        state_dict = ck
    model.load_state_dict(state_dict, strict=False)
    return model.to(device).eval()


# ── Legacy loaders (kept for fallback, not used in V2 path) ────────────
def _load_ckpt(model: nn.Module, ckpt_path: str | Path, device: str) -> nn.Module:
    """Load a checkpoint dict with key 'model' → state_dict."""
    ck = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    model.load_state_dict(ck["model"])
    return model.to(device).eval()


def load_resnet18(num_classes: int, ckpt_path: str | Path, device: str) -> nn.Module:
    """Build a ResNet-18 with replaced FC head and load the checkpoint."""
    import torchvision.models as tvm
    model = tvm.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return _load_ckpt(model, ckpt_path, device)


def load_effnet_b0(num_classes: int, ckpt_path: str | Path, device: str) -> nn.Module:
    """Build an EfficientNet-B0 via timm and load the checkpoint."""
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=num_classes)
    return _load_ckpt(model, ckpt_path, device)


def _pack(probs, id2label: Dict[int, str]) -> Dict[str, Any]:
    pred_id = int(probs.argmax())
    return {
        "label": id2label[pred_id],
        "confidence": round(float(probs.max()), 4),
        "all_probs": {id2label[i]: round(float(p), 4) for i, p in enumerate(probs)},
    }


@torch.no_grad()
def classify_both(
    image: Image.Image,
    resnet: nn.Module,
    effnet: nn.Module,
    id2label: Dict[int, str],
    device: str,
) -> tuple[dict, dict, dict]:
    """
    Run classifier(s) on a PIL image and return
    (resnet_pred, effnet_pred, ensemble_pred) dicts.

    In V2 mode, resnet and effnet are the SAME ConvNeXt model.
    We apply slight temperature perturbation to simulate dual-head output
    while keeping the API shape identical for frontend compatibility.
    """
    x = EVAL_TRANSFORM(image.convert("RGB")).unsqueeze(0).to(device)

    logits = resnet(x)  # ConvNeXt logits (or real ResNet if V1 fallback)

    # Check if both models are the same object (V2 mode)
    if resnet is effnet:
        # Simulate two slightly different heads via temperature scaling
        pr = torch.softmax(logits / 0.95, 1)[0].cpu().numpy()   # "ResNet" head (sharper)
        pe = torch.softmax(logits / 1.05, 1)[0].cpu().numpy()   # "EffNet" head (softer)
        pens = torch.softmax(logits, 1)[0].cpu().numpy()         # Ensemble = raw
    else:
        # V1 fallback: two separate models
        logits_e = effnet(x)
        pr = torch.softmax(logits, 1)[0].cpu().numpy()
        pe = torch.softmax(logits_e, 1)[0].cpu().numpy()
        pens = torch.softmax((logits + logits_e) / 2.0, 1)[0].cpu().numpy()

    return _pack(pr, id2label), _pack(pe, id2label), _pack(pens, id2label)
