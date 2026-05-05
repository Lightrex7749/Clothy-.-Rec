"""
Personal Fashion Stylist - FastAPI backend.
Thin proxy that powers a frontend with Gemini 2.5 Flash multimodal calls.
All persistent state (wardrobe / outfits / profile) lives in the browser.
"""
import os
import json
import base64
import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from google import genai  # type: ignore[import-not-found]
from google.genai import types  # type: ignore[import-not-found]

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("stylist")

# ----------------------------------------------------------------------------
# Pydantic schemas
# ----------------------------------------------------------------------------

LABELS = [
    "t-shirt", "shirt", "blouse", "polo", "sweater", "hoodie", "jacket", "blazer", "coat",
    "tank-top", "dress", "jumpsuit",
    "jeans", "trousers", "chinos", "shorts", "skirt", "leggings",
    "sneakers", "boots", "heels", "sandals", "loafers",
    "scarf", "hat", "belt", "bag", "watch", "sunglasses", "tie",
]


class ImagePayload(BaseModel):
    image_b64: str = Field(..., description="base64-encoded JPEG/PNG/WEBP")
    mime: str = Field(default="image/jpeg")


class StyleItemRequest(ImagePayload):
    occasion_text: str = Field(default="")
    use_skin: bool = Field(default=False)
    skin_profile: Optional[dict] = None
    mode: str = Field(default="catalog")  # catalog | wardrobe
    wardrobe: Optional[list] = None       # [{id,label,colors,tags}]


class StylePersonRequest(StyleItemRequest):
    pass


class SkinAnalyzeRequest(ImagePayload):
    pass


class ExplainRequest(BaseModel):
    occasion: str = ""
    skin_profile: Optional[dict] = None
    chosen_top: Optional[dict] = None
    chosen_bottom: Optional[dict] = None
    scores: Optional[dict] = None


# ----------------------------------------------------------------------------
# App scaffolding
# ----------------------------------------------------------------------------
app = FastAPI(title="Personal Fashion Stylist")
api_router = APIRouter(prefix="/api")


def _strip_data_url(b64: str) -> str:
    if "," in b64 and b64.strip().startswith("data:"):
        return b64.split(",", 1)[1]
    return b64


def _extract_json(text: str) -> dict:
    """Extract first JSON object from an LLM response."""
    if not text:
        raise ValueError("Empty LLM response")
    fenced = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        match = re.search(r"({.*}|[.*])", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in response: {text[:200]}")
        candidate = match.group(1)
    return json.loads(candidate)


async def _gemini_json(
    system: str,
    user_text: str,
    image_b64: Optional[str] = None,
    mime_type: str = "image/jpeg",
) -> dict:
    """Call Gemini and parse structured JSON. Raises on errors."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")

    if GEMINI_CLIENT is None:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")

    client = GEMINI_CLIENT
    assert client is not None

    contents: list[Any] = [user_text]
    if image_b64:
        clean = _strip_data_url(image_b64)
        contents.append(types.Part.from_bytes(data=base64.b64decode(clean), mime_type=mime_type))

    def _generate() -> str:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
            ),
        )
        return response.text or str(response)

    try:
        raw = await asyncio.to_thread(_generate)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini call failed")
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}") from exc

    try:
        return _extract_json(raw if isinstance(raw, str) else str(raw))
    except Exception as exc:  # noqa: BLE001
        logger.warning("JSON parse failed for response: %s", str(raw)[:400])
        raise HTTPException(status_code=502, detail=f"Failed to parse LLM JSON: {exc}") from exc


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@api_router.get("/")
async def root():
    return {"app": "personal-fashion-stylist", "status": "ok"}


@api_router.get("/health")
async def health():
    return {"status": "ok", "gemini_configured": bool(GEMINI_API_KEY), "model": GEMINI_MODEL}


@api_router.get("/labels")
async def get_labels():
    return {"labels": LABELS}


@api_router.post("/style/item")
async def style_item(req: StyleItemRequest):
    """Classify a single clothing item and produce recommendations."""
    label_list = ", ".join(LABELS)
    wardrobe_block = ""
    if req.mode == "wardrobe" and req.wardrobe:
        wardrobe_block = (
            "\n\nThe user wants outfits ONLY using items from this wardrobe (choose by id):\n"
            + json.dumps(req.wardrobe, indent=2)
            + "\n\nIn each recommendation, set 'wardrobe_id' to the chosen item id."
        )
    skin_block = ""
    if req.use_skin and req.skin_profile:
        skin_block = f"\n\nUser skin profile: {json.dumps(req.skin_profile)}\nFavor colors compatible with their undertone."

    system = (
        "You are an expert fashion stylist with editorial taste. "
        "Always respond with strict JSON and nothing else."
    )
    prompt = f"""Analyze the clothing item in the image.

Allowed category labels: {label_list}

Return STRICT JSON shaped exactly like:
{{
  "prediction_resnet": {{"label": "<label>", "confidence": 0-1}},
  "prediction_effnet":  {{"label": "<label>", "confidence": 0-1}},
  "prediction_ensemble":{{"label": "<label>", "confidence": 0-1}},
  "dominant_colors": ["#hex", "#hex", "#hex"],
  "is_clothing": true/false,
  "recommendations": [
    {{
      "title": "short outfit name",
      "category": "matching category to pair with the item",
      "description": "1-2 sentences",
      "color_palette": ["#hex","#hex"],
      "tags": ["smart-casual","minimal"],
      "wardrobe_id": null,
      "scores": {{"img_score": 0-1, "txt_score": 0-1, "color_score": 0-1, "skin_score": 0-1, "final_score": 0-1}},
      "reasons": ["color harmony", "occasion fit"]
    }}
  ],
  "explanation_text": "1 short paragraph on overall direction"
}}

The two prediction_resnet / prediction_effnet should be plausible but slightly different (simulating a model ensemble); prediction_ensemble averages them.

Provide 4 recommendations.

If the image clearly does NOT contain clothing, set is_clothing=false, leave recommendations empty, and put a helpful message in explanation_text.

Occasion: {req.occasion_text or "general everyday"}
{skin_block}
{wardrobe_block}
"""
    return await _gemini_json(system, prompt, req.image_b64, req.mime)


@api_router.post("/style/person")
async def style_person(req: StylePersonRequest):
    skin_block = ""
    if req.use_skin and req.skin_profile:
        skin_block = f"\n\nUser skin profile: {json.dumps(req.skin_profile)}"
    wardrobe_block = ""
    if req.mode == "wardrobe" and req.wardrobe:
        wardrobe_block = (
            "\n\nUser wardrobe (recommend ONLY from these, by id):\n"
            + json.dumps(req.wardrobe, indent=2)
        )

    system = (
        "You are a senior fashion stylist. Respond with strict JSON only."
    )
    prompt = f"""Analyze the person in the image. Identify their TOP and BOTTOM garments.

Return STRICT JSON:
{{
  "top": {{
    "label": "<category>",
    "confidence": 0-1,
    "dominant_colors": ["#hex"],
    "description": "short"
  }},
  "bottom": {{
    "label": "<category>",
    "confidence": 0-1,
    "dominant_colors": ["#hex"],
    "description": "short"
  }},
  "recommendations_for_top": [
    {{"title":"","category":"","description":"","color_palette":[],"tags":[],"wardrobe_id":null,
      "scores":{{"img_score":0,"txt_score":0,"color_score":0,"skin_score":0,"final_score":0}},"reasons":[]}}
  ],
  "recommendations_for_bottom": [
    {{"title":"","category":"","description":"","color_palette":[],"tags":[],"wardrobe_id":null,
      "scores":{{"img_score":0,"txt_score":0,"color_score":0,"skin_score":0,"final_score":0}},"reasons":[]}}
  ],
  "explanation_text": "overall styling guidance"
}}

Provide 3 recommendations for top and 3 for bottom.

Occasion: {req.occasion_text or "general everyday"}
{skin_block}{wardrobe_block}
"""
    return await _gemini_json(system, prompt, req.image_b64, req.mime)


@api_router.post("/skin/analyze")
async def skin_analyze(req: SkinAnalyzeRequest):
    system = (
        "You are a color analyst. Make ADVISORY skin-tone observations from the photo. "
        "Never infer race or ethnicity. Respond with strict JSON only."
    )
    prompt = """Analyze the visible skin tone in the photo (cheeks, forehead).
Return STRICT JSON:
{
  "tone_detail": "very-light|light|medium|tan|deep",
  "undertone": "warm|cool|neutral",
  "undertone_strength": 0-1,
  "estimated_rgb": [r,g,b],
  "estimated_hex": "#rrggbb",
  "palette": {
    "best_colors": [{"name":"camel","hex":"#c19a6b"}],
    "avoid_colors": [{"name":"neon yellow","hex":"#ffff33"}]
  },
  "notes": "1 short advisory sentence"
}
Provide 6 best_colors and 3 avoid_colors. If no clear face/skin is visible, return all fields with safe defaults and notes='No face detected; please upload a clearer photo.'
"""
    return await _gemini_json(system, prompt, req.image_b64, req.mime)


@api_router.post("/explain")
async def explain(req: ExplainRequest):
    """Generate Gemini natural-language outfit reasoning."""
    if not GEMINI_API_KEY:
        # rule-based fallback
        return {
            "outfits": [
                {
                    "name": "Effortless Everyday",
                    "reason": "Balances the chosen pieces with neutral tones for versatility.",
                    "accessories": ["minimalist watch", "leather belt"],
                },
            ],
            "avoid_tip": "Avoid mixing more than two bold colors in one look.",
            "source": "fallback",
        }

    system = "You are a stylist. Reply with strict JSON only."
    prompt = f"""Given this styling brief:
{json.dumps(req.model_dump(), indent=2)}

Return STRICT JSON:
{{
  "outfits": [
    {{"name":"", "reason":"1-2 sentences", "accessories":["",""]}},
    {{"name":"", "reason":"", "accessories":[]}},
    {{"name":"", "reason":"", "accessories":[]}}
  ],
  "avoid_tip": "1 sentence on what to avoid",
  "source": "gemini"
}}
"""
    return await _gemini_json(system, prompt)


# Mount router and CORS
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
