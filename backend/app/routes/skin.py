"""ClothyRec – Skin analysis route."""
from PIL import Image
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import get_settings
from app.services.skin_service import analyze_skin

router = APIRouter(prefix="/api/skin")

@router.post("/analyze")
async def skin_analyze(image: UploadFile = File(...)):
    """Analyze skin tone from a face/selfie photo."""
    try:
        img = Image.open(image.file).convert("RGB")
    except Exception:
        raise HTTPException(400, "Could not read image.")
    cfg = get_settings()
    return analyze_skin(img, device=cfg.DEVICE)
