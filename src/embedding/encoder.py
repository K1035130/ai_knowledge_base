"""sentence-transformers wrapper: text -> vectors, with on-disk caching."""

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import EMBEDDING_DIR, EMBEDDING_MODEL  # noqa: E402


@lru_cache(maxsize=1)
def get_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def encode_texts(texts: list[str], model_name: str = EMBEDDING_MODEL) -> np.ndarray:
    model = get_model(model_name)
    return model.encode(texts, show_progress_bar=True, normalize_embeddings=True)


def encode_and_save(df: pd.DataFrame, text_col: str, out_name: str) -> np.ndarray:
    embeddings = encode_texts(df[text_col].tolist())
    np.save(EMBEDDING_DIR / out_name, embeddings)
    return embeddings
