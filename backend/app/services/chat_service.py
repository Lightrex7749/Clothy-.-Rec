import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger("clothyrec.services.chat")

def _get_client() -> Optional[genai.Client]:
    from app.config import get_settings
    cfg = get_settings()
    if not cfg.GEMINI_API_KEY:
        return None
    return genai.Client(api_key=cfg.GEMINI_API_KEY)

async def generate_chat_response(
    message: str,
    history: List[Dict[str, str]],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a response from Gemini based on the conversation history and ML context.
    """
    client = _get_client()
    if not client:
        return "I am an AI stylist, but my Gemini API key is not configured. Please check the server settings."

    # Construct the system instruction
    system_instruction = (
        "You are 'Atelier', an elite AI Personal Fashion Stylist. "
        "You have access to the user's latest wardrobe analysis, skin profile, and saved outfits. "
        "Your tone should be sophisticated, encouraging, and highly knowledgeable about fashion, color theory, and styling. "
        "Provide concise, direct advice. "
    )

    if context:
        system_instruction += "\n\n--- CURRENT USER CONTEXT ---\n"
        system_instruction += "You must use this data to inform your answers if relevant.\n"
        system_instruction += json.dumps(context, indent=2)
        system_instruction += "\n--------------------------\n"

    # Convert history to Gemini format
    contents = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn["content"])]))
    
    # Add the current message
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

    from app.config import get_settings
    cfg = get_settings()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def _call_gemini() -> str:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            )
        )
        return response.text or "I'm sorry, I couldn't generate a response."

    try:
        reply = await asyncio.to_thread(_call_gemini)
        return reply
    except Exception as e:
        logger.exception("Failed to generate chat response")
        return f"I'm sorry, my styling core experienced an error: {e}"
