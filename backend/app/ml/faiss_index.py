"""
ClothyRec – FAISS index helpers.

Loads the master index and builds top-only / bottom-only sub-indices
at startup so searches are already scoped by clothing direction.
"""

from __future__ import annotations

import faiss
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple


def load_master_index(index_path: str | Path) -> faiss.Index:
    """Load a serialised FAISS IndexFlatIP."""
    return faiss.read_index(str(index_path))


def build_subset_index(
    embeddings_all: np.ndarray,
    meta: pd.DataFrame,
    class_set: set[str],
) -> Tuple[faiss.Index, np.ndarray]:
    """
    Build a FAISS sub-index from rows whose label is in `class_set`.

    Returns
    -------
    sub_index : faiss.IndexFlatIP
    meta_indices : np.ndarray   mapping sub-index row → master meta row
    """
    mask = meta["label"].isin(class_set)
    meta_indices = meta.index[mask].to_numpy()
    sub_emb = embeddings_all[meta_indices].astype("float32")

    D = embeddings_all.shape[1]
    sub_index = faiss.IndexFlatIP(D)
    sub_index.add(sub_emb)
    return sub_index, meta_indices


def search_index(
    index: faiss.Index,
    query_vec: np.ndarray,
    meta_indices: np.ndarray,
    k: int = 150,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Search a sub-index and return (scores, global_meta_rows).

    Parameters
    ----------
    index        : the FAISS sub-index to search
    query_vec    : (1, D) float32 normalised query
    meta_indices : mapping from sub-index rows → global meta rows
    k            : how many candidates to retrieve

    Returns
    -------
    scores     : (k,) float array of inner-product scores
    meta_rows  : (k,) int array of global meta row indices
    """
    k = min(k, index.ntotal)
    scores, idxs = index.search(query_vec, k)
    global_rows = meta_indices[idxs[0]]
    return scores[0], global_rows
