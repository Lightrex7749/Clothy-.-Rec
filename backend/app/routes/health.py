"""ClothyRec – Health & labels routes."""
from fastapi import APIRouter
from app.ml.singleton import get_registry
from app.config import get_settings

router = APIRouter()

@router.get("/health")
async def health():
    cfg = get_settings()
    try:
        reg = get_registry()
        return {"status": "ok", "models_loaded": True, "device": reg.device,
                "num_classes": reg.num_classes, "index_size": reg.embeddings_all.shape[0],
                "v2_mode": reg.v2_mode}
    except Exception:
        return {"status": "ok", "models_loaded": False, "device": cfg.DEVICE, "v2_mode": False}

@router.get("/labels")
async def labels():
    reg = get_registry()
    return {"labels": reg.label_list, "top_classes": sorted(get_settings().TOP_CLASSES),
            "bottom_classes": sorted(get_settings().BOTTOM_CLASSES),
            "v2_mode": reg.v2_mode}
