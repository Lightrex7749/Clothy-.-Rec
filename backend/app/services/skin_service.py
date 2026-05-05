"""
ClothyRec – Skin tone analysis service.

Uses MTCNN for face detection, samples cheek regions, applies
YCrCb skin masking, then classifies undertone via Lab colour space.
"""
from __future__ import annotations
import cv2, logging, numpy as np
from PIL import Image
from typing import Any, Dict

logger = logging.getLogger("clothyrec.skin")
_mtcnn = None

def _get_mtcnn(device="cpu"):
    global _mtcnn
    if _mtcnn is None:
        from facenet_pytorch import MTCNN
        _mtcnn = MTCNN(keep_all=True, device=device)
        logger.info("MTCNN loaded")
    return _mtcnn

def _clamp(v, lo, hi):
    return max(lo, min(hi, int(v)))

def _skin_mask_ycrcb(roi_bgr):
    ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    mask = (Cr >= 133) & (Cr <= 173) & (Cb >= 77) & (Cb <= 127) & (Y > 30) & (Y < 245)
    return mask

# Palette recommendations by undertone
PALETTES = {
    "warm": {
        "best": [
            {"name": "camel", "hex": "#C19A6B"},
            {"name": "olive", "hex": "#808000"},
            {"name": "coral", "hex": "#FF7F50"},
            {"name": "warm beige", "hex": "#D4A574"},
            {"name": "terracotta", "hex": "#E2725B"},
            {"name": "golden yellow", "hex": "#FFD700"},
        ],
        "avoid": [
            {"name": "icy blue", "hex": "#99CCFF"},
            {"name": "magenta", "hex": "#FF00FF"},
            {"name": "neon pink", "hex": "#FF6EC7"},
        ],
    },
    "cool": {
        "best": [
            {"name": "navy", "hex": "#000080"},
            {"name": "charcoal", "hex": "#36454F"},
            {"name": "lavender", "hex": "#E6E6FA"},
            {"name": "dusty rose", "hex": "#DCAE96"},
            {"name": "emerald", "hex": "#50C878"},
            {"name": "slate blue", "hex": "#6A5ACD"},
        ],
        "avoid": [
            {"name": "orange", "hex": "#FFA500"},
            {"name": "neon yellow", "hex": "#FFFF33"},
            {"name": "rust", "hex": "#B7410E"},
        ],
    },
    "neutral": {
        "best": [
            {"name": "white", "hex": "#FFFFFF"},
            {"name": "true red", "hex": "#FF0000"},
            {"name": "jade green", "hex": "#00A86B"},
            {"name": "soft pink", "hex": "#FFB6C1"},
            {"name": "teal", "hex": "#008080"},
            {"name": "medium grey", "hex": "#808080"},
        ],
        "avoid": [
            {"name": "neon green", "hex": "#39FF14"},
            {"name": "bright orange", "hex": "#FF4500"},
            {"name": "hot pink", "hex": "#FF69B4"},
        ],
    },
}

def analyze_skin(image: Image.Image, device: str = "cpu") -> Dict[str, Any]:
    """Analyze skin tone from a face/selfie image."""
    img_rgb = np.array(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    mtcnn = _get_mtcnn(device)
    boxes, probs, _ = mtcnn.detect(Image.fromarray(img_rgb), landmarks=True)

    if boxes is None or len(boxes) == 0:
        return {
            "tone_detail": "unknown",
            "undertone": "neutral",
            "undertone_strength": 0.0,
            "rgb": [200, 180, 160],
            "hex": "#C8B4A0",
            "palette": PALETTES["neutral"],
            "notes": "No face detected. Please upload a clearer, front-facing photo.",
        }

    best_i = int(np.argmax(probs))
    fx1, fy1, fx2, fy2 = [int(v) for v in boxes[best_i]]
    h, w = img_bgr.shape[:2]
    fx1, fy1 = _clamp(fx1, 0, w-2), _clamp(fy1, 0, h-2)
    fx2, fy2 = _clamp(fx2, fx1+2, w), _clamp(fy2, fy1+2, h)
    bw, bh = fx2-fx1, fy2-fy1

    # Cheek regions
    cy1, cy2 = fy1 + int(0.45*bh), fy1 + int(0.70*bh)
    lx1, lx2 = fx1 + int(0.15*bw), fx1 + int(0.40*bw)
    rx1, rx2 = fx1 + int(0.60*bw), fx1 + int(0.85*bw)

    pixels = []
    for (cx1, cx2) in [(lx1, lx2), (rx1, rx2)]:
        roi = img_bgr[cy1:cy2, cx1:cx2]
        if roi.size == 0:
            continue
        mask = _skin_mask_ycrcb(roi)
        if mask.sum() < 80:
            mask = np.ones(mask.shape, dtype=bool)
        pixels.append(roi[mask])

    if not pixels:
        return {"tone_detail": "unknown", "undertone": "neutral", "undertone_strength": 0.0,
                "rgb": [200,180,160], "hex": "#C8B4A0", "palette": PALETTES["neutral"],
                "notes": "Could not sample skin pixels. Try a better-lit photo."}

    pixels_arr = np.vstack(pixels).astype(np.uint8)
    lab = cv2.cvtColor(pixels_arr.reshape(-1,1,3), cv2.COLOR_BGR2LAB).reshape(-1,3)
    L_mean, _a, b_mean = lab.mean(axis=0)
    delta_b = b_mean - 128

    # Undertone
    if delta_b > 6: undertone = "warm"
    elif delta_b < -6: undertone = "cool"
    else: undertone = "neutral"
    strength = min(abs(delta_b) / 20.0, 1.0)

    # Tone detail
    if L_mean >= 190: tone = "very light"
    elif L_mean >= 170: tone = "light"
    elif L_mean >= 135: tone = "medium"
    elif L_mean >= 110: tone = "tan"
    else: tone = "deep"

    # Mean RGB
    mean_bgr = pixels_arr.mean(axis=0).astype(int)
    r, g, b = int(mean_bgr[2]), int(mean_bgr[1]), int(mean_bgr[0])
    hex_color = f"#{r:02X}{g:02X}{b:02X}"

    return {
        "tone_detail": tone,
        "undertone": undertone,
        "undertone_strength": round(float(strength), 3),
        "rgb": [r, g, b],
        "hex": hex_color,
        "palette": PALETTES.get(undertone, PALETTES["neutral"]),
        "notes": f"Advisory: {tone} skin with {undertone} undertone (strength {strength:.0%}). Lighting may affect accuracy.",
    }
