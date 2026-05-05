"""ClothyRec – Chat route for Gemini AI Stylist."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.chat_service import generate_chat_response

router = APIRouter(prefix="/api/chat")

class ChatTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatTurn] = []
    context: Optional[Dict[str, Any]] = None

@router.post("")
async def chat_endpoint(req: ChatRequest):
    """Chat with the Gemini AI stylist."""
    try:
        history_dicts = [{"role": t.role, "content": t.content} for t in req.history]
        reply = await generate_chat_response(req.message, history_dicts, req.context)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
