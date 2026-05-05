"""
ClothyRec – CNN classifier loading & inference.

Loads ResNet-18 and EfficientNet-B0 checkpoints and provides a single
`classify_both` helper that returns predictions from all three "heads"
(ResNet, EffNet, Ensemble).
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torchvision.models as tvm
import torchvision.transforms as T
import timm
from PIL import Image
from pathlib import Path
from typing import Dict, Any


# ── ImageNet normalisation (same as training) ──────────────────────────
EVAL_TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
])


def _load_ckpt(model: nn.Module, ckpt_path: str | Path, device: str) -> nn.Module:
    """Load a checkpoint dict with key 'model' → state_dict."""
    ck = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    model.load_state_dict(ck["model"])
    return model.to(device).eval()


def load_resnet18(num_classes: int, ckpt_path: str | Path, device: str) -> nn.Module:
    """Build a ResNet-18 with replaced FC head and load the checkpoint."""
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
    Run both classifiers on a PIL image and return
    (resnet_pred, effnet_pred, ensemble_pred) dicts.
    """
    x = EVAL_TRANSFORM(image.convert("RGB")).unsqueeze(0).to(device)

    logits_r = resnet(x)
    logits_e = effnet(x)

    pr = torch.softmax(logits_r, 1)[0].cpu().numpy()
    pe = torch.softmax(logits_e, 1)[0].cpu().numpy()
    pens = torch.softmax((logits_r + logits_e) / 2.0, 1)[0].cpu().numpy()

    return _pack(pr, id2label), _pack(pe, id2label), _pack(pens, id2label)
