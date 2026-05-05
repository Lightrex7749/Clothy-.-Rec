"""
ClothyRec – meta.csv path repair.

The original meta.csv contains Colab absolute paths like:
  /root/.cache/kagglehub/.../dataset_clean/casual_shirts/img_001.jpg

This module strips everything before 'dataset_clean/' to get a relative path,
then reconstructs the absolute path using the configured DATA_ROOT.
"""

from __future__ import annotations

import os
import pandas as pd
import logging

logger = logging.getLogger("clothyrec.path_repair")


def repair_paths(meta: pd.DataFrame, data_root: str) -> pd.DataFrame:
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

    # Extract relative path after "dataset_clean/"
    def _to_relative(p: str) -> str:
        p = str(p).replace("\\", "/")
        marker = "dataset_clean/"
        if marker in p:
            return p.split(marker, 1)[1]
        # Already a relative path or unknown format — return as-is
        return p

    meta["rel_path"] = meta["path"].apply(_to_relative)

    if data_root:
        data_root = str(data_root).replace("\\", "/").rstrip("/")
        # Ensure data_root ends at dataset_clean level
        if not data_root.endswith("dataset_clean"):
            # Check if dataset_clean is inside data_root
            candidate = os.path.join(data_root, "dataset_clean")
            if os.path.isdir(candidate):
                data_root = candidate.replace("\\", "/")

        meta["path"] = meta["rel_path"].apply(
            lambda r: os.path.join(data_root, r).replace("\\", "/")
        )
        # Verify a sample
        sample_path = meta.iloc[0]["path"]
        if os.path.exists(sample_path):
            logger.info("Path repair OK — sample exists: %s", sample_path)
        else:
            logger.warning(
                "Path repair WARNING — sample does NOT exist: %s  "
                "(images won't be servable until DATA_ROOT is correct)",
                sample_path,
            )
    else:
        logger.warning(
            "DATA_ROOT not set — image paths will be relative only. "
            "Set DATA_ROOT env var to the folder containing dataset_clean/."
        )
        meta["path"] = meta["rel_path"]

    return meta
