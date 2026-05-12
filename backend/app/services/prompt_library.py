"""ClothyRec – Prompt library loader."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List

from app.config import get_settings

logger = logging.getLogger("clothyrec.services.prompt_library")


_PROMPT_START = re.compile(r"^\s*(\d+)\.(.*)$")


def _parse_prompts(text: str) -> List[Dict[str, str]]:
    prompts: List[Dict[str, str]] = []
    current_id: str | None = None
    current_lines: List[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        match = _PROMPT_START.match(line)
        if match:
            if current_id is not None:
                prompt_text = "\n".join(current_lines).strip()
                if prompt_text:
                    prompts.append({"id": current_id, "prompt": prompt_text})
            current_id = match.group(1)
            first_line = match.group(2).strip()
            current_lines = [first_line] if first_line else []
            continue

        if current_id is not None:
            if line or current_lines:
                current_lines.append(line)

    if current_id is not None:
        prompt_text = "\n".join(current_lines).strip()
        if prompt_text:
            prompts.append({"id": current_id, "prompt": prompt_text})

    return prompts


def _image_sort_key(path: Path) -> int:
    name = path.name
    match = re.search(r"\((\d+)\)", name)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)", name)
    if match:
        return int(match.group(1))
    return 9999


def load_prompt_library() -> Dict[str, List[Dict[str, str]]]:
    cfg = get_settings()
    prompt_dir = cfg.get_v2_dir() / "prompt_data"
    prompts_path = prompt_dir / "prompts.txt"

    if not prompts_path.is_file():
        logger.warning("prompts.txt not found at %s", prompts_path)
        return {"prompts": []}

    prompts = _parse_prompts(prompts_path.read_text(encoding="utf-8"))

    image_files = sorted(
        [p for p in prompt_dir.iterdir() if p.is_file() and p.name.lower() != "prompts.txt"],
        key=_image_sort_key,
    )

    for i, prompt in enumerate(prompts):
        image_url = ""
        if i < len(image_files):
            image_url = f"/static/prompts/{image_files[i].name}"
        prompt["image_url"] = image_url

    return {"prompts": prompts}
