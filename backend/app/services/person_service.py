"""
ClothyRec – Person (full-body) styling service.

Uses YOLOv8s-pose to detect keypoints, crop top/bottom garments,
then runs the item pipeline on each crop.
"""
from __future__ import annotations
import cv2, logging, numpy as np, uuid
from PIL import Image
from typing import Any, Dict, Optional
from app.config import get_settings
from app.services.style_service import process_item

logger = logging.getLogger("clothyrec.person")
_yolo_model = None

def _get_yolo():
    global _yolo_model
    if _yolo_model is None:
        cfg = get_settings()
        from ultralytics import YOLO
        model_path = cfg.get_yolo_pose_model_path()
        model_path.parent.mkdir(parents=True, exist_ok=True)
        _yolo_model = YOLO(str(model_path))
        logger.info("YOLO pose model loaded: %s", model_path)
    return _yolo_model

def _clamp(v, lo, hi):
    return int(max(lo, min(hi, v)))

def _crop_top_bottom(img_bgr):
    H, W = img_bgr.shape[:2]
    res = _get_yolo().predict(img_bgr, conf=0.25, verbose=False)[0]
    if res.keypoints is None or len(res.keypoints) == 0:
        raise ValueError("No person detected. Upload a clearer full-body photo.")
    best = int(np.argmax(res.boxes.conf.cpu().numpy()))
    kpts = res.keypoints.xy[best].cpu().numpy()
    x1, y1, x2, y2 = map(int, res.boxes.xyxy[best].cpu().numpy())
    def safe(pts):
        g = ~np.isnan(pts[:,0]) & ~np.isnan(pts[:,1]) & (pts[:,0]>1) & (pts[:,1]>1)
        return pts[g] if g.any() else pts
    sh = safe(kpts[[5,6]]); hp = safe(kpts[[11,12]]); ak = safe(kpts[[15,16]])
    if sh.size and hp.size:
        ty1,ty2 = min(sh[:,1].min(),hp[:,1].min()), hp[:,1].max()
        tx1,tx2 = min(sh[:,0].min(),hp[:,0].min()), max(sh[:,0].max(),hp[:,0].max())
    else:
        tx1,ty1,tx2,ty2 = x1,y1,x2,(y1+y2)//2
    if hp.size and ak.size:
        by1,by2 = hp[:,1].min(), ak[:,1].max()
        bx1,bx2 = min(hp[:,0].min(),ak[:,0].min()), max(hp[:,0].max(),ak[:,0].max())
    else:
        bx1,by1,bx2,by2 = x1,(y1+y2)//2,x2,y2
    px, py = int(0.10*(x2-x1)), int(0.08*(y2-y1))
    c = _clamp
    top = img_bgr[c(ty1-py,0,H-1):c(ty2+py,0,H-1), c(tx1-px,0,W-1):c(tx2+px,0,W-1)].copy()
    bot = img_bgr[c(by1-py,0,H-1):c(by2+py,0,H-1), c(bx1-px,0,W-1):c(bx2+px,0,W-1)].copy()
    return top, bot

def process_person(image: Image.Image, occasion_text="", use_skin=False, skin_profile=None) -> Dict[str, Any]:
    cfg = get_settings()
    upload_dir = cfg.get_upload_dir()
    img_bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    try:
        top_bgr, bot_bgr = _crop_top_bottom(img_bgr)
    except ValueError as e:
        return {"error": str(e), "top_crop_url": None, "bottom_crop_url": None, "top_results": None, "bottom_results": None}
    uid = uuid.uuid4().hex[:8]
    tp, bp = upload_dir/f"top_{uid}.jpg", upload_dir/f"bot_{uid}.jpg"
    cv2.imwrite(str(tp), top_bgr); cv2.imwrite(str(bp), bot_bgr)
    top_pil = Image.fromarray(cv2.cvtColor(top_bgr, cv2.COLOR_BGR2RGB))
    bot_pil = Image.fromarray(cv2.cvtColor(bot_bgr, cv2.COLOR_BGR2RGB))
    tr = process_item(top_pil, occasion_text, "catalog", use_skin, skin_profile)
    br = process_item(bot_pil, occasion_text, "catalog", use_skin, skin_profile)
    return {"error": None, "top_crop_url": f"/static/uploads/{tp.name}", "bottom_crop_url": f"/static/uploads/{bp.name}", "top_results": tr, "bottom_results": br}
