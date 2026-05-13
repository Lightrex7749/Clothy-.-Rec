"""ClothyRec – Prompt library route."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.prompt_library import load_prompt_library

router = APIRouter(prefix="/api/prompts")


@router.get("")
async def get_prompts():
    return load_prompt_library()
