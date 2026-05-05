"""ClothyRec – Style routes (item + person)."""
from __future__ import annotations
import uuid, logging
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.config import get_settings
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
    img = _read_image(image)
    upload_url = _save_upload(img, cfg.get_upload_dir())
    skin_profile = {"undertone": skin_undertone} if use_skin else None
    result = process_item(img, occasion_text, mode, use_skin, skin_profile)
    result["upload_url"] = upload_url

    # Add image_url for each recommendation
    for rec in result.get("recommendations", []):
        img_path = rec.get("image_path", "")
        if img_path:
            rec["image_url"] = f"/static/dataset/{rec.get('rel_path', '')}"
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
    upload_url = _save_upload(img, cfg.get_upload_dir())
    skin_profile = {"undertone": skin_undertone} if use_skin else None
    result = process_person(img, occasion_text, use_skin, skin_profile)
    result["upload_url"] = upload_url

    # Add image_url for recs in both top and bottom results
    for key in ["top_results", "bottom_results"]:
        sub = result.get(key)
        if sub:
            for rec in sub.get("recommendations", []):
                rec["image_url"] = f"/static/dataset/{rec.get('rel_path', '')}"
    return result
