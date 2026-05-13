"""Pre-download and cache the YOLO pose model."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.config import get_settings
from ultralytics import YOLO


def main() -> None:
    cfg = get_settings()
    model_path = cfg.get_yolo_pose_model_path()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    YOLO(str(model_path))
    print(f"YOLO pose model ready: {model_path}")


if __name__ == "__main__":
    main()
