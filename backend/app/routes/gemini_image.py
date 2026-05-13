"""Gemini image generation route."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.services.image_gen_service import generate_images
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/api/gemini/image")
cfg = get_settings()
_image_limit = rate_limit(cfg.GEMINI_IMAGE_RPM, "gemini_image", cfg.GEMINI_RATE_WINDOW_SEC)


@router.post("", dependencies=[Depends(_image_limit)])
async def generate_image(
    image: UploadFile = File(...),
    prompt: str = Form(""),
    style_prompt: str = Form(""),
    style: str = Form(""),
    count: int = Form(4),
):
    """Generate styled images from a user photo + prompt."""
    try:
        img_bytes = await image.read()
        result = await generate_images(
            image_bytes=img_bytes,
            mime_type=image.content_type or "image/jpeg",
            user_prompt=prompt,
            style_prompt=style_prompt,
            count=count,
        )
        result["style"] = style
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
