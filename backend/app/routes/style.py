"""ClothyRec – Style routes (item + person)."""
from __future__ import annotations
import uuid, logging
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.config import get_settings
from app.ml.singleton import get_registry
from app.services.style_service import process_item
from app.services.person_service import process_person

logger = logging.getLogger("clothyrec.routes.style")
router = APIRouter(prefix="/api/style")

def _read_image(file: UploadFile) -> Image.Image:
    try:
        return Image.open(file.file).convert("RGB")
    except Exception:
        raise HTTPException(400, "Could not read uploaded image. Ensure it is a valid JPEG/PNG.")

def _save_upload(image: Image.Image, upload_dir: Path) -> str:
    name = f"upload_{uuid.uuid4().hex[:8]}.jpg"
    path = upload_dir / name
    image.save(str(path), "JPEG", quality=90)
    return f"/static/uploads/{name}"

def _patch_image_urls(recs: list, v2_mode: bool):
    """Ensure each recommendation has a usable image_url."""
    for rec in recs:
        # V2 service already sets image_url; V1 fallback uses rel_path
        if not rec.get("image_url"):
            rel_path = rec.get("rel_path", "")
            rec["image_url"] = f"/static/dataset/{rel_path}" if rel_path else ""

@router.post("/item")
async def style_item(
    image: UploadFile = File(...),
    occasion_text: str = Form(""),
    mode: str = Form("catalog"),
    use_skin: bool = Form(False),
    skin_undertone: str = Form("neutral"),
):
    """Classify a single clothing item and return matching recommendations."""
    cfg = get_settings()
    reg = get_registry()
    img = _read_image(image)
    upload_url = _save_upload(img, cfg.get_upload_dir())
    skin_profile = {"undertone": skin_undertone} if use_skin else None
    result = process_item(img, occasion_text, mode, use_skin, skin_profile)
    result["upload_url"] = upload_url

    # Patch image URLs for recommendations
    _patch_image_urls(result.get("recommendations", []), reg.v2_mode)
    return result

@router.post("/person")
async def style_person(
    image: UploadFile = File(...),
    occasion_text: str = Form(""),
    use_skin: bool = Form(False),
    skin_undertone: str = Form("neutral"),
):
    """Analyze a full-body photo: crop top/bottom + recommend for each."""
    img = _read_image(image)
    cfg = get_settings()
    reg = get_registry()
    upload_url = _save_upload(img, cfg.get_upload_dir())
    skin_profile = {"undertone": skin_undertone} if use_skin else None
    result = process_person(img, occasion_text, use_skin, skin_profile)
    result["upload_url"] = upload_url

    # Patch image URLs for recs in both top and bottom results
    for key in ["top_results", "bottom_results"]:
        sub = result.get(key)
        if sub:
            _patch_image_urls(sub.get("recommendations", []), reg.v2_mode)
    return result
