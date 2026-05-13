"""Smoke tests for Gemini endpoints without API keys."""
from __future__ import annotations

import os

from fastapi.testclient import TestClient


def _client_without_keys() -> TestClient:
    os.environ["GEMINI_CHAT_API_KEY"] = ""
    os.environ["GEMINI_IMAGE_API_KEY"] = ""
    os.environ["GEMINI_API_KEY"] = ""

    from app import config as config_module

    config_module.get_settings.cache_clear()
    from app.main import app

    return TestClient(app)


def test_gemini_chat_fallback():
    client = _client_without_keys()
    res = client.post(
        "/api/gemini/text/chat",
        json={"message": "hi", "history": [], "context": None},
    )
    assert res.status_code == 200
    payload = res.json()
    assert "reply" in payload
    assert "GEMINI_CHAT_API_KEY" in payload["reply"]


def test_gemini_optimize_fallback():
    client = _client_without_keys()
    res = client.post(
        "/api/gemini/text/optimize",
        json={"prompt": "black blazer", "gender": "male", "instructions": None},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("optimized_prompt") == "black blazer"


def test_gemini_image_requires_key():
    client = _client_without_keys()
    res = client.post(
        "/api/gemini/image",
        data={"prompt": "streetwear", "style_prompt": "editorial", "count": "1"},
        files={"image": ("photo.jpg", b"fake", "image/jpeg")},
    )
    assert res.status_code == 500
    assert "GEMINI_IMAGE_API_KEY" in res.text
