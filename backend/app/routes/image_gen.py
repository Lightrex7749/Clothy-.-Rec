"""ClothyRec – Gemini image generation route."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.image_gen_service import generate_images

router = APIRouter(prefix="/api/generate")


@router.post("/image")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
