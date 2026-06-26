"""KMeans + c-TF-IDF topic labeling. Swap in BERTopic later if elbow/KMeans isn't enough."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import RANDOM_SEED  # noqa: E402


def find_best_k(embeddings: np.ndarray, k_range=range(2, 15)) -> dict[int, float]:
    """Inertia per k for the elbow method."""
    inertias = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init="auto")
        km.fit(embeddings)
        inertias[k] = km.inertia_
    return inertias


def kmeans_cluster(embeddings: np.ndarray, k: int) -> np.ndarray:
    km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init="auto")
    return km.fit_predict(embeddings)


def top_terms_per_cluster(texts: pd.Series, labels: np.ndarray, top_n: int = 10) -> dict[int, list[str]]:
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
    tfidf = vectorizer.fit_transform(texts)
    terms = vectorizer.get_feature_names_out()

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
