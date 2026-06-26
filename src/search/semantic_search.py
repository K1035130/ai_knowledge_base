"""Brute-force cosine-similarity search over cached embeddings. Swap in FAISS/Chroma later."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.embedding.encoder import encode_texts  # noqa: E402


def cosine_similarity(query_vec: np.ndarray, corpus_vecs: np.ndarray) -> np.ndarray:
    query_vec = query_vec / np.linalg.norm(query_vec)
    corpus_norms = corpus_vecs / np.linalg.norm(corpus_vecs, axis=1, keepdims=True)
    return corpus_norms @ query_vec


def search(query: str, df: pd.DataFrame, corpus_vecs: np.ndarray, top_k: int = 5) -> pd.DataFrame:
    query_vec = encode_texts([query])[0]
    scores = cosine_similarity(query_vec, corpus_vecs)
    top_idx = np.argsort(scores)[::-1][:top_k]

    result = df.iloc[top_idx].copy()
    result["score"] = scores[top_idx]
    return result
