"""ClothyRec – Prompt library route."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.prompt_library import load_prompt_library
from app.services.chat_service import optimize_prompt

router = APIRouter(prefix="/api/prompts")


class PromptOptimizeRequest(BaseModel):
    prompt: str
    gender: str
    instructions: str | None = None


@router.get("")
async def get_prompts():
    return load_prompt_library()


@router.post("/optimize")
async def optimize_prompt_endpoint(req: PromptOptimizeRequest):
    optimized = await optimize_prompt(req.prompt, req.gender, req.instructions)
    return {"optimized_prompt": optimized}
