"""ClothyRec – Gemini image generation service."""
from __future__ import annotations

import asyncio
import base64
import colorsys
import hashlib
import io
import logging
import random
import textwrap
from typing import List, Optional, Tuple

from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings

logger = logging.getLogger("clothyrec.services.image_gen")


def _get_client() -> Optional[genai.Client]:
    cfg = get_settings()
    api_key = cfg.GEMINI_IMAGE_API_KEY or cfg.GEMINI_CHAT_API_KEY or cfg.GEMINI_API_KEY
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


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


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "SegoeUI.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _color_from_seed(seed: int, hue_offset: float, lightness: float, saturation: float) -> Tuple[int, int, int]:
    rnd = random.Random(seed)
    hue = (rnd.random() + hue_offset) % 1.0
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return int(r * 255), int(g * 255), int(b * 255)


def _render_placeholder_image(
    prompt: str,
    style_prompt: str,
    variant: int,
    size: Tuple[int, int] = (768, 1024),
) -> Tuple[bytes, str]:
    seed = int(hashlib.sha256(f"{prompt}|{style_prompt}|{variant}".encode("utf-8")).hexdigest()[:8], 16)
    width, height = size
    base_a = _color_from_seed(seed, 0.0, 0.18, 0.55)
    base_b = _color_from_seed(seed, 0.35, 0.12, 0.65)
    accent = _color_from_seed(seed, 0.6, 0.4, 0.7)

    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(base_a[0] * (1 - t) + base_b[0] * t)
        g = int(base_a[1] * (1 - t) + base_b[1] * t)
        b = int(base_a[2] * (1 - t) + base_b[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    draw.ellipse(
        (-width * 0.2, -height * 0.15, width * 0.9, height * 0.85),
        outline=(accent[0], accent[1], accent[2], 140),
        width=6,
    )

    rng = random.Random(seed + 13)
    for _ in range(160):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        alpha = rng.randint(8, 24)
        draw.point((x, y), fill=(255, 255, 255, alpha))

    panel_h = int(height * 0.28)
    draw.rectangle((0, height - panel_h, width, height), fill=(0, 0, 0, 180))

    title_font = _load_font(28)
    body_font = _load_font(16)
    small_font = _load_font(12)

    draw.text((40, height - panel_h + 22), f"Atelier Preview {variant + 1}", fill=(255, 255, 255, 230), font=title_font)

    desc = (prompt or "Concept look in progress").strip()
    if style_prompt:
        desc = f"{desc} / {style_prompt.strip()}"
    lines = textwrap.wrap(desc, width=52)
    text_y = height - panel_h + 70
    for line in lines[:3]:
        draw.text((40, text_y), line, fill=(220, 220, 220, 220), font=body_font)
        text_y += 22

    draw.text(
        (40, height - 30),
        "Gemini quota reached - showing concept placeholders.",
        fill=(180, 180, 180, 200),
        font=small_font,
    )

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue(), "image/png"


def _is_quota_error(err: Exception) -> bool:
    message = str(err).lower()
    return (
        "resource_exhausted" in message
        or "quota" in message
        or "rate limit" in message
        or "429" in message
    )


async def generate_images(
    image_bytes: bytes,
    mime_type: str,
    user_prompt: str,
    style_prompt: str,
    count: int = 4,
) -> dict:
    cfg = get_settings()
    client = _get_client()
    if not client:
        raise RuntimeError("GEMINI_IMAGE_API_KEY not configured on server")

    model_name = cfg.GEMINI_IMAGE_MODEL or cfg.GEMINI_MODEL
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
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

    data_urls: List[str] = []
    try:
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
    except Exception as e:
        if _is_quota_error(e):
            logger.warning("Gemini quota exhausted. Returning placeholder images.")
            fallback = [
                _to_data_url(*_render_placeholder_image(final_prompt, style_prompt, i))
                for i in range(count)
            ]
            return {
                "images": fallback,
                "model": model_name,
                "prompt": final_prompt,
                "fallback": True,
                "message": "Gemini quota exhausted. Showing concept placeholders.",
            }
        raise
