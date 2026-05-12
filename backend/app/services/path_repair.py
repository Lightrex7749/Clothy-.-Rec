"""
ClothyRec – meta.csv path repair.

The original meta.csv contains Colab/Kaggle absolute paths.
This module repairs them to local paths using the configured roots.

V2 adds support for the combined metadata which has:
  - Ecommerce rows: /kaggle/input/fashion-product-images-small/images/{id}.jpg
  - DeepFashion rows: /root/.cache/kagglehub/.../img_highres/MEN/{category}/{item_id}/{filename}
"""

from __future__ import annotations

import os
import re
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger("clothyrec.path_repair")

# Legacy runtime prefixes from Colab/Kaggle/Cloud notebooks
_LEGACY_PREFIXES = ("/kaggle/input/", "/root/.cache/", "/content/")


def _clean_path(p: str) -> str:
    return str(p).replace("\\", "/").strip()


def _has_legacy_prefix(p: str) -> bool:
    p = _clean_path(p)
    return any(prefix in p for prefix in _LEGACY_PREFIXES)


def _looks_absolute(p: str) -> bool:
    p = _clean_path(p)
    return Path(p).is_absolute() or bool(re.match(r"^[A-Za-z]:", p))


class PathNormalizer:
    """Centralized normalization for metadata image paths."""

    def __init__(
        self,
        base_dir: Path | None = None,
        data_root: str | Path | None = None,
        v2_dir: str | Path | None = None,
    ) -> None:
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = Path(base_dir).resolve()
        self.repo_root = self.base_dir.parent

        self.data_root = self._resolve_data_root(data_root)
        self.v2_dir = Path(v2_dir).resolve() if v2_dir else None
        self.v2_ecom_dir = (
            self.v2_dir / "datasets" / "fashion_products" / "images"
            if self.v2_dir else None
        )
        self.v2_df_dir = (
            self.v2_dir / "datasets" / "deepfashion_subset"
            if self.v2_dir else None
        )

    def _resolve_data_root(self, data_root: str | Path | None) -> Path | None:
        if data_root:
            root = Path(data_root).expanduser()
            if root.name != "dataset_clean":
                candidate = root / "dataset_clean"
                if candidate.is_dir():
                    root = candidate
            return root

        candidate = self.repo_root / "data" / "dataset_clean"
        if candidate.is_dir():
            return candidate
        return None

    def _join(self, base: Path | None, rel: str) -> str:
        rel = _clean_path(rel).lstrip("/")
        if not rel:
            return ""
        if base:
            return str((base / rel)).replace("\\", "/")
        return rel

    def normalize_v1_path(self, raw_path: str) -> Dict[str, str]:
        p = _clean_path(raw_path)
        rel = ""

        if "dataset_clean/" in p:
            rel = p.split("dataset_clean/", 1)[1]
        else:
            # If absolute but no marker, fall back to basename
            rel = Path(p).name if _looks_absolute(p) else p

        rel = _clean_path(rel).lstrip("/")
        image_url = f"/static/dataset/{rel}" if rel else ""
        abs_path = self._join(self.data_root, rel)

        return {"path": abs_path, "rel_path": rel, "image_url": image_url}

    def normalize_v2_ecommerce_row(self, row: pd.Series) -> Dict[str, str]:
        img_path = _clean_path(row.get("image_path", row.get("path", "")))
        fname = Path(img_path).name if img_path else ""
        if not fname and pd.notna(row.get("id")):
            try:
                fname = f"{int(row['id'])}.jpg"
            except Exception:
                fname = ""

        rel = f"fashion_products/images/{fname}" if fname else ""
        return {
            "path": self._join(self.v2_ecom_dir, fname),
            "rel_path": rel,
            "image_url": f"/static/v2/ecommerce/{fname}" if fname else "",
        }

    def normalize_v2_deepfashion_row(self, row: pd.Series) -> Dict[str, str]:
        img_path = _clean_path(row.get("image_path", row.get("path", "")))
        rel = ""

        if "img_highres/" in img_path:
            rel = img_path.split("img_highres/", 1)[1]
        elif "deepfashion_subset/" in img_path:
            rel = img_path.split("deepfashion_subset/", 1)[1]
        else:
            gender = str(row.get("gender", "")).upper().strip()
            if gender not in {"MEN", "WOMEN"}:
                if "/MEN/" in img_path:
                    gender = "MEN"
                elif "/WOMEN/" in img_path:
                    gender = "WOMEN"

            category = str(row.get("category", "")).strip()
            item_id = str(row.get("item_id", "")).strip()
            filename = str(row.get("filename", "")).strip() or Path(img_path).name

            if gender and category and item_id and filename:
                rel = f"{gender}/{category}/{item_id}/{filename}"
            elif filename:
                rel = filename

        rel = _clean_path(rel).lstrip("/")
        rel_path = f"deepfashion_subset/{rel}" if rel else ""
        return {
            "path": self._join(self.v2_df_dir, rel),
            "rel_path": rel_path,
            "image_url": f"/static/v2/deepfashion/{rel}" if rel else "",
        }


# ── articleType → V2 unified label mapping ─────────────────────────────
_ARTICLE_TYPE_TO_LABEL = {
    # Topwear → tops
    "tshirts": "tshirt",
    "shirts": "shirt",
    "sweatshirts": "hoodie",
    "sweaters": "sweater",
    "jackets": "jacket",
    "blazers": "jacket",
    "rain jacket": "jacket",
    "nehru jackets": "jacket",
    "waistcoat": "jacket",
    # Bottomwear → bottoms
    "jeans": "jeans",
    "trousers": "pants",
    "track pants": "pants",
    "shorts": "pants",
    "capris": "pants",
    "chinos": "pants",
    "leggings": "pants",
    "jeggings": "jeans",
    "tracksuits": "pants",
}


def derive_v2_labels(meta: pd.DataFrame) -> pd.DataFrame:
    """
    Fill in missing `label` values for ecommerce rows using articleType.
    DeepFashion rows already have labels from the V2 pipeline.
    """
    meta = meta.copy()

    # Normalise source column
    meta["source"] = meta["source"].fillna("ecommerce")

    # For ecommerce rows missing labels, derive from articleType
    mask = (meta["label"].isna()) & (meta["articleType"].notna())
    if mask.any():
        meta.loc[mask, "label"] = (
            meta.loc[mask, "articleType"]
            .str.lower()
            .str.strip()
            .map(_ARTICLE_TYPE_TO_LABEL)
        )

    # Still-missing labels: try subCategory
    still_missing = meta["label"].isna()
    if still_missing.any():
        sub_map = {
            "topwear": "shirt",      # generic fallback
            "bottomwear": "pants",   # generic fallback
        }
        meta.loc[still_missing, "label"] = (
            meta.loc[still_missing, "subCategory"]
            .str.lower()
            .str.strip()
            .map(sub_map)
        )

    return meta


def repair_v2_paths(
    meta: pd.DataFrame,
    v2_dir: str | Path,
    base_dir: Path | None = None,
) -> pd.DataFrame:
    """
    Repair paths in the V2 combined metadata.

    Parameters
    ----------
    meta    : DataFrame from combined_metadata.csv
    v2_dir  : path to PersonalFashionStylistV2/ directory

    Returns
    -------
    DataFrame with repaired 'path' and 'rel_path' columns.
    """
    meta = meta.copy()
    normalizer = PathNormalizer(base_dir=base_dir, v2_dir=v2_dir)

    legacy_series = None
    if "image_path" in meta.columns:
        legacy_series = meta["image_path"]
    elif "path" in meta.columns:
        legacy_series = meta["path"]

    if legacy_series is not None:
        legacy_count = legacy_series.apply(_has_legacy_prefix).sum()
        if legacy_count:
            logger.info("Detected %d legacy runtime paths in V2 metadata", int(legacy_count))

    # Ensure we have a working 'path' column (copy from image_path if missing)
    if "path" not in meta.columns:
        meta["path"] = meta.get("image_path", "")

    meta["rel_path"] = ""
    meta["image_url"] = ""

    # ── Ecommerce rows ─────────────────────────────────────────────────
    ecom_mask = meta["source"] == "ecommerce"
    if ecom_mask.any():
        ecom_paths = meta.loc[ecom_mask].apply(normalizer.normalize_v2_ecommerce_row, axis=1)
        ecom_df = pd.DataFrame(list(ecom_paths), index=meta.loc[ecom_mask].index)
        meta.loc[ecom_mask, ["path", "rel_path", "image_url"]] = ecom_df[["path", "rel_path", "image_url"]]

    # ── DeepFashion rows ───────────────────────────────────────────────
    df_mask = meta["source"] == "deepfashion"
    if df_mask.any():
        df_paths = meta.loc[df_mask].apply(normalizer.normalize_v2_deepfashion_row, axis=1)
        df_df = pd.DataFrame(list(df_paths), index=meta.loc[df_mask].index)
        meta.loc[df_mask, ["path", "rel_path", "image_url"]] = df_df[["path", "rel_path", "image_url"]]

    # ── Verify a sample ────────────────────────────────────────────────
    for source_name in ["ecommerce", "deepfashion"]:
        sample_mask = meta["source"] == source_name
        if sample_mask.any():
            sample_path = meta.loc[sample_mask, "path"].iloc[0]
            if os.path.exists(sample_path):
                logger.info("V2 path repair OK (%s) - sample: %s", source_name, sample_path)
            else:
                logger.warning(
                    "V2 path repair WARNING (%s) - sample NOT found: %s",
                    source_name, sample_path,
                )

    return meta


def repair_paths(
    meta: pd.DataFrame,
    data_root: str,
    base_dir: Path | None = None,
) -> pd.DataFrame:
    """
    Repair absolute Colab paths in meta['path'] to local paths.

    Parameters
    ----------
    meta      : DataFrame with a 'path' column containing old absolute paths
    data_root : local path to the 'dataset_clean/' directory
                e.g. "C:/Users/HP/.cache/kagglehub/.../dataset_clean"

    Returns
    -------
    DataFrame with repaired 'path' column.  Also adds 'rel_path' column.
    """
    meta = meta.copy()
    normalizer = PathNormalizer(base_dir=base_dir, data_root=data_root)

    if "path" not in meta.columns:
        meta["path"] = ""

    legacy_count = meta["path"].apply(_has_legacy_prefix).sum()
    if legacy_count:
        logger.info("Detected %d legacy runtime paths in V1 metadata", int(legacy_count))

    normalized = meta["path"].apply(normalizer.normalize_v1_path)
    meta["path"] = normalized.apply(lambda v: v["path"])
    meta["rel_path"] = normalized.apply(lambda v: v["rel_path"])
    meta["image_url"] = normalized.apply(lambda v: v["image_url"])
    meta["source"] = meta.get("source", "legacy")

    # Verify a sample
    sample_path = meta.iloc[0]["path"] if len(meta) else ""
    if sample_path and os.path.exists(sample_path):
        logger.info("Path repair OK — sample exists: %s", sample_path)
    elif normalizer.data_root:
        logger.warning(
            "Path repair WARNING — sample does NOT exist: %s  "
            "(check local dataset placement)",
            sample_path,
        )
    else:
        logger.warning(
            "DATA_ROOT not resolved — image paths will be relative only. "
            "Place data/dataset_clean in the repo or set DATA_ROOT."
        )

    return meta
