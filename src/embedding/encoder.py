"""Embeds conversation text via SiliconFlow's embedding API.

Used to run a local sentence-transformers model here, but its weights alone (~470MB in fp32)
left no headroom in Render's 512MB free-tier memory limit. Calling a hosted embedding API
instead trades local compute for a network call, which the pipeline already depends on for
cluster naming and highlights anyway. (Originally Gemini's API; moved to SiliconFlow's
BAAI/bge-m3 after Gemini's access policy changed.)
"""

import sys
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import EMBEDDING_DIM, EMBEDDING_DIR, EMBEDDING_MODEL  # noqa: E402
from src.llm.siliconflow_client import embed_texts  # noqa: E402
from src.utils.concurrency import map_ordered  # noqa: E402

_BATCH_SIZE = 32  # conservative: the API caps both items and total tokens per request
# bge-m3 accepts 8192 tokens per input and rejects (400) anything longer, which would kill a whole
# report build. A joined conversation can easily run past that, so cut it here — Chinese is roughly
# one token per character, the worst case, so 6000 chars stays inside the limit either way.
# The opening of a conversation carries the topic, which is all the clustering downstream needs.
_MAX_DOC_CHARS = 6000
# Batches are fanned out concurrently (see map_ordered). Kept deliberately modest: the point is
# to overlap latency, and these are the token-heavy calls in the build (~50k tokens each), so
# pushing past the provider's TPM limit would turn into 429s whose backoff costs far more than
# the concurrency saves.
_MAX_WORKERS = 8


def encode_texts(texts: list[str], model_name: str = EMBEDDING_MODEL) -> np.ndarray:
    texts = [t[:_MAX_DOC_CHARS] for t in texts]
    batches = [texts[i : i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)]
    if not batches:
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

    # Ordered fan-out keeps every vector aligned with its input text.
    batch_results = map_ordered(partial(embed_texts, model=model_name), batches, _MAX_WORKERS)

    arr = np.array([v for batch in batch_results for v in batch], dtype=np.float32)
    # L2-normalize so KMeans' Euclidean distance behaves like cosine similarity,
    # matching the previous sentence-transformers setup (normalize_embeddings=True).
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def encode_and_save(df: pd.DataFrame, text_col: str, out_name: str) -> np.ndarray:
    embeddings = encode_texts(df[text_col].tolist())
    np.save(EMBEDDING_DIR / out_name, embeddings)
    return embeddings
