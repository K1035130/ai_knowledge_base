"""Embeds conversation text via Gemini's embedding API.

Used to run a local sentence-transformers model here, but its weights alone (~470MB in fp32)
left no headroom in Render's 512MB free-tier memory limit. Calling Gemini's embedding API
instead trades local compute for a network call, which the pipeline already depends on for
cluster naming and highlights anyway.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import EMBEDDING_DIR, EMBEDDING_MODEL  # noqa: E402
from src.llm.gemini_client import embed_texts  # noqa: E402

_BATCH_SIZE = 100  # conservative batch size — the API's per-request limit isn't publicly pinned down
_OUTPUT_DIM = 768  # gemini-embedding-001 defaults to 3072-dim; 768 is plenty for KMeans on a personal-size corpus


def encode_texts(texts: list[str], model_name: str = EMBEDDING_MODEL) -> np.ndarray:
    vectors: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        vectors.extend(embed_texts(batch, model=model_name, output_dimensionality=_OUTPUT_DIM))

    arr = np.array(vectors, dtype=np.float32)
    # L2-normalize so KMeans' Euclidean distance behaves like cosine similarity,
    # matching the previous sentence-transformers setup (normalize_embeddings=True).
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def encode_and_save(df: pd.DataFrame, text_col: str, out_name: str) -> np.ndarray:
    embeddings = encode_texts(df[text_col].tolist())
    np.save(EMBEDDING_DIR / out_name, embeddings)
    return embeddings
