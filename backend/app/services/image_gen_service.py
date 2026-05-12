"""ClothyRec – Gemini image generation service."""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from typing import List, Optional, Tuple

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger("clothyrec.services.image_gen")


def _get_client() -> Optional[genai.Client]:
    cfg = get_settings()
    if not cfg.GEMINI_API_KEY:
        return None
    return genai.Client(api_key=cfg.GEMINI_API_KEY)


def _build_prompt(style_prompt: str, user_prompt: str) -> str:
    parts = []
    if style_prompt:
        parts.append(style_prompt.strip())
    if user_prompt:
        parts.append(user_prompt.strip())
    return " ".join(p for p in parts if p).strip()


def _extract_images(response) -> List[Tuple[bytes, str]]:
    images: List[Tuple[bytes, str]] = []
    for cand in getattr(response, "candidates", []) or []:
        content = getattr(cand, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
            if not inline:
                continue
            data = getattr(inline, "data", None)
            if not data:
                continue
            mime = getattr(inline, "mime_type", None) or "image/png"
            if isinstance(data, str):
                data_bytes = base64.b64decode(data)
            else:
                data_bytes = data
            images.append((data_bytes, mime))
    return images


def _to_data_url(data: bytes, mime: str) -> str:
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


async def generate_images(
    image_bytes: bytes,
    mime_type: str,
    user_prompt: str,
    style_prompt: str,
    count: int = 4,
) -> dict:
    client = _get_client()
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured on server")

    model_name = os.environ.get("GEMINI_IMAGE_MODEL") or os.environ.get("GEMINI_MODEL", "") or "nano-banana"
    if not model_name:
        raise RuntimeError("GEMINI_IMAGE_MODEL not configured on server")

    final_prompt = _build_prompt(style_prompt, user_prompt)
    if not final_prompt:
        raise RuntimeError("Prompt is required")

    count = max(1, min(int(count), 6))

    parts = [
        types.Part.from_text(text=final_prompt),
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type or "image/jpeg"),
    ]
    contents = [types.Content(role="user", parts=parts)]

    def _call_once():
        return client.models.generate_content(
            model=model_name,
            contents=contents,
        )

    data_urls: List[str] = []
    for _ in range(count):
        response = await asyncio.to_thread(_call_once)
        images = _extract_images(response)
        if not images:
            logger.warning("No image data returned from model")
            continue
        for data, mime in images:
            data_urls.append(_to_data_url(data, mime))
            if len(data_urls) >= count:
                break
        if len(data_urls) >= count:
            break

    if not data_urls:
        raise RuntimeError(
            "No images returned. Ensure GEMINI_IMAGE_MODEL is image-capable. "
            f"Current model: {model_name}"
        )

    return {"images": data_urls, "model": model_name, "prompt": final_prompt}
