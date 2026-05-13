"""Benchmark YOLO pose models on a single image."""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.config import get_settings
from ultralytics import YOLO


def resolve_model_path(name: str, models_dir: Path) -> Path:
    model_path = Path(name)
    if model_path.is_absolute():
        return model_path
    if model_path.suffix:
        return models_dir / model_path.name
    return models_dir / f"{name}.pt"


def benchmark(model_name: str, image_path: str, runs: int, warmup: int) -> None:
    cfg = get_settings()
    models_dir = cfg.get_models_dir()
    model_path = resolve_model_path(model_name, models_dir)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))
    for _ in range(max(warmup, 0)):
        model.predict(image_path, conf=0.25, verbose=False)

    timings = []
    for _ in range(runs):
        start = perf_counter()
        model.predict(image_path, conf=0.25, verbose=False)
        timings.append(perf_counter() - start)

    avg = statistics.mean(timings)
    p95 = statistics.quantiles(timings, n=20)[-1] if len(timings) >= 20 else max(timings)
    print(f"{model_name}: avg={avg:.3f}s p95={p95:.3f}s (runs={runs})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark YOLO pose models on one image")
    parser.add_argument("--image", required=True, help="Path to a full-body test image")
    parser.add_argument(
        "--models",
        default="yolov8n-pose.pt,yolov8s-pose.pt,yolov8m-pose.pt",
        help="Comma-separated model names or paths",
    )
    parser.add_argument("--runs", type=int, default=5, help="Benchmark runs per model")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per model")
    args = parser.parse_args()

    model_list = [m.strip() for m in args.models.split(",") if m.strip()]
    for name in model_list:
        benchmark(name, args.image, args.runs, args.warmup)


if __name__ == "__main__":
    main()
