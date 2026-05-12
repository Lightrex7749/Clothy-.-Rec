"""
ClothyRec – FAISS index helpers.

Loads the master index and builds top-only / bottom-only sub-indices
at startup so searches are already scoped by clothing direction.

V2 adds duplicate suppression and similarity threshold filtering.
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


def search_with_dedup(
    index: faiss.Index,
    query_vec: np.ndarray,
    meta_indices: np.ndarray,
    embeddings_all: np.ndarray,
    k: int = 200,
    sim_threshold: float = 0.15,
    dedup_threshold: float = 0.98,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Search with duplicate suppression and similarity threshold filtering.

    Parameters
    ----------
    index           : the FAISS sub-index to search
    query_vec       : (1, D) float32 normalised query
    meta_indices    : mapping from sub-index rows → global meta rows
    embeddings_all  : full embedding matrix for dedup checks
    k               : how many raw candidates to retrieve
    sim_threshold   : drop results with score below this
    dedup_threshold : suppress results whose mutual similarity exceeds this

    Returns
    -------
    scores     : filtered & deduplicated scores
    meta_rows  : corresponding global meta row indices
    """
    raw_scores, raw_rows = search_index(index, query_vec, meta_indices, k)

    # 1. Similarity threshold
    keep_mask = raw_scores >= sim_threshold
    scores = raw_scores[keep_mask]
    rows = raw_rows[keep_mask]

    if len(scores) == 0:
        return scores, rows

    # 2. Duplicate suppression (greedy)
    deduped_idx = [0]
    deduped_embs = [embeddings_all[rows[0]]]

    for i in range(1, len(rows)):
        candidate = embeddings_all[rows[i]]
        # Check against all already-accepted embeddings
        sims = np.array([float(candidate @ ref) for ref in deduped_embs])
        if np.all(sims < dedup_threshold):
            deduped_idx.append(i)
            deduped_embs.append(candidate)

    deduped_idx = np.array(deduped_idx)
    return scores[deduped_idx], rows[deduped_idx]
