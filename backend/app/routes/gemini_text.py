"""Gemini text routes for chat and prompt optimization."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.services.chat_service import generate_chat_response, optimize_prompt
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/api/gemini/text")
cfg = get_settings()
_chat_limit = rate_limit(cfg.GEMINI_CHAT_RPM, "gemini_chat", cfg.GEMINI_RATE_WINDOW_SEC)
_opt_limit = rate_limit(cfg.GEMINI_CHAT_RPM, "gemini_opt", cfg.GEMINI_RATE_WINDOW_SEC)


class ChatTurn(BaseModel):
    role: str
    content: str


class GeminiChatRequest(BaseModel):
    message: str
    history: List[ChatTurn] = []
    context: Optional[Dict[str, Any]] = None


class PromptOptimizeRequest(BaseModel):
    prompt: str
    gender: str
    instructions: Optional[str] = None


@router.post("/chat", dependencies=[Depends(_chat_limit)])
async def chat_endpoint(req: GeminiChatRequest):
    """Chat with the Gemini AI stylist."""
    try:
        history_dicts = [{"role": t.role, "content": t.content} for t in req.history]
        reply = await generate_chat_response(req.message, history_dicts, req.context)
        return {"reply": reply}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/optimize", dependencies=[Depends(_opt_limit)])
async def optimize_prompt_endpoint(req: PromptOptimizeRequest):
    """Optimize a prompt for Gemini image generation."""
    try:
        optimized = await optimize_prompt(req.prompt, req.gender, req.instructions)
        return {"optimized_prompt": optimized}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
