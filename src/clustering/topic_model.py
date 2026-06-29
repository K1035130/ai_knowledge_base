"""KMeans + c-TF-IDF topic labeling. Swap in BERTopic later if elbow/KMeans isn't enough."""

import sys
from pathlib import Path

import jieba
import numpy as np
import pandas as pd
import stopwordsiso
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import RANDOM_SEED  # noqa: E402
from src.utils.memlog import log_rss  # noqa: E402

# Only "text" (a pure LaTeX-rendering artifact) is noise — math symbols like
# frac/cdot/sin/theta are kept since they're a real signal that a cluster is math-related.
STOPWORDS = list(ENGLISH_STOP_WORDS | stopwordsiso.stopwords("zh") | {"text"})


def find_best_k(embeddings: np.ndarray, k_range: range = range(6, 13)) -> dict[int, float]:
    """Inertia per k for the elbow method. Default range stays narrow (6-12) because wider
    ranges let KMeans carve out clusters that are only coincidentally co-occurring topics
    rather than coherent ones."""
    inertias = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init="auto")
        km.fit(embeddings)
        inertias[k] = km.inertia_
    return inertias


def select_k_kneedle(inertias: dict[int, float]) -> int:
    """Pick the k whose (k, inertia) point sits farthest from the line joining the first and last points."""
    ks = np.array(list(inertias.keys()), dtype=float)
    values = np.array(list(inertias.values()), dtype=float)
    x_norm = (ks - ks.min()) / (ks.max() - ks.min())
    y_norm = (values - values.min()) / (values.max() - values.min())
    line_vec = np.array([x_norm[-1] - x_norm[0], y_norm[-1] - y_norm[0]])
    line_vec /= np.linalg.norm(line_vec)
    distances = []
    for xi, yi in zip(x_norm, y_norm):
        point_vec = np.array([xi - x_norm[0], yi - y_norm[0]])
        proj = np.dot(point_vec, line_vec) * line_vec
        distances.append(np.linalg.norm(point_vec - proj))
    keys = list(inertias.keys())
    return keys[int(np.argmax(distances))]


def kmeans_cluster(embeddings: np.ndarray, k: int) -> np.ndarray:
    km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init="auto")
    return km.fit_predict(embeddings)


def top_terms_per_cluster(texts: pd.Series, labels: np.ndarray, top_n: int = 10) -> dict[int, list[str]]:
    log_rss("before jieba tokenization (jieba's dict loads lazily on first call)")
    tokenized = [" ".join(jieba.cut(text)) for text in texts]
    log_rss("after jieba tokenization")
    vectorizer = TfidfVectorizer(max_features=2000, stop_words=STOPWORDS)
    tfidf = vectorizer.fit_transform(tokenized)
    terms = vectorizer.get_feature_names_out()
    log_rss("after TF-IDF vectorization")

    result = {}
    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        cluster_scores = tfidf[mask].mean(axis=0).A1
        top_idx = cluster_scores.argsort()[::-1][:top_n]
        result[cluster_id] = [terms[i] for i in top_idx]
    return result


def bertopic_cluster(texts: list[str], embeddings: np.ndarray | None = None):
    """Optional path — uncomment bertopic in requirements.txt and pip install first."""
    from bertopic import BERTopic

    model = BERTopic()
    topics, probs = model.fit_transform(texts, embeddings=embeddings)
    return model, topics, probs
