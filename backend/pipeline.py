"""Orchestrates the full report-build pipeline: parse -> clean -> profile -> embed -> cluster -> label -> highlights.

Mirrors the logic validated interactively in notebooks/01_eda.ipynb, but calls the (now-fixed)
src/ modules instead of duplicating the logic here.
"""

import gc
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.analysis import usage_profile as up  # noqa: E402
from src.clustering import topic_model as tm  # noqa: E402
from src.embedding import encoder  # noqa: E402
from src.llm.gemini_client import label_cluster, summarize_highlight  # noqa: E402
from src.parsing.chatgpt_parser import parse_exports  # noqa: E402
from src.utils.memlog import log_rss  # noqa: E402

ProgressCallback = Callable[[str], None]

_STEPS = {
    "zh": {
        "parse": "解析对话文件",
        "clean": "清洗时间戳异常点",
        "profile": "计算使用画像统计",
        "embed": "生成对话向量",
        "cluster": "聚类话题",
        "label": "用 Gemini 给话题簇命名",
        "monthly_share": "计算月度话题占比",
        "highlights": "生成每月高光小结",
        "done": "完成",
    },
    "en": {
        "parse": "Parsing conversation files",
        "clean": "Cleaning up timestamp outliers",
        "profile": "Computing usage profile stats",
        "embed": "Embedding conversations",
        "cluster": "Clustering topics",
        "label": "Naming topic clusters with Gemini",
        "monthly_share": "Computing monthly topic share",
        "highlights": "Writing monthly highlights",
        "done": "Done",
    },
}


def _series_to_native(series: pd.Series, value_type: type = int) -> dict:
    return {str(k): value_type(v) for k, v in series.items()}


def build_report(
    export_paths: list[Path],
    lang: str = "zh",
    timezone: str = "UTC",
    on_progress: ProgressCallback = lambda step: None,
) -> dict:
    steps = _STEPS["en"] if lang == "en" else _STEPS["zh"]

    on_progress(steps["parse"])
    df = parse_exports(export_paths)
    df = up.add_time_features(df, timezone=timezone)
    log_rss("after parsing")

    on_progress(steps["clean"])
    clean_df = up.clean_timestamps(df)
    del df  # clean_timestamps returns a new frame; the original is a near-duplicate we no longer need
    gc.collect()
    log_rss("after cleaning + freeing raw df")

    on_progress(steps["profile"])
    session = up.session_duration(clean_df)
    thread = up.thread_span(clean_df)
    rt = up.response_times(clean_df)
    overview = {
        "total_conversations": int(clean_df["conversation_id"].nunique()),
        "total_messages": int(len(clean_df)),
        "active_days": int(clean_df["timestamp"].dt.date.nunique()),
        "avg_session_minutes": round(session.mean().total_seconds() / 60, 1) if len(session) else 0,
        "longest_session_minutes": round(session.max().total_seconds() / 60, 1) if len(session) else 0,
        "avg_thread_span_hours": round(thread.mean().total_seconds() / 3600, 1) if len(thread) else 0,
        "avg_response_seconds": round(rt.mean().total_seconds(), 1) if len(rt) else 0,
    }
    activity = {
        "by_hour": _series_to_native(up.activity_by_hour(clean_df)),
        "by_weekday": _series_to_native(up.activity_by_weekday(clean_df)),
        "by_month": _series_to_native(up.monthly_trend(clean_df)),
    }
    language_ratio = _series_to_native(up.language_ratio(clean_df), value_type=float)
    rewrite_rate = up.rewrite_rate_stats(clean_df)
    log_rss("after usage profile stats")

    on_progress(steps["embed"])
    conv_docs = clean_df.groupby("conversation_id")["text"].apply(lambda t: " ".join(t)).reset_index()
    conv_docs.columns = ["conversation_id", "doc"]
    embeddings = encoder.encode_texts(conv_docs["doc"].tolist())
    log_rss("after embedding")

    on_progress(steps["cluster"])
    inertias = tm.find_best_k(embeddings)
    best_k = tm.select_k_kneedle(inertias)
    labels = tm.kmeans_cluster(embeddings, best_k)
    conv_docs["cluster"] = labels
    log_rss("after kmeans, before c-TF-IDF")
    top_terms = tm.top_terms_per_cluster(conv_docs["doc"], labels)
    log_rss("after c-TF-IDF keyword extraction")

    on_progress(steps["label"])
    cluster_info = []
    for cluster_id, keywords in top_terms.items():
        count = int((conv_docs["cluster"] == cluster_id).sum())
        cluster_info.append(
            {
                "id": int(cluster_id),
                "label": label_cluster(keywords, lang=lang),
                "count": count,
                "keywords": keywords[:6],
            }
        )

    on_progress(steps["monthly_share"])
    conv_start = clean_df.groupby("conversation_id")["timestamp"].min()
    conv_docs["start_month"] = conv_docs["conversation_id"].map(conv_start).dt.to_period("M").astype(str)
    monthly_topic = conv_docs.groupby(["start_month", "cluster"]).size().unstack(fill_value=0)
    monthly_topic_share = monthly_topic.div(monthly_topic.sum(axis=1), axis=0)
    monthly_topic_share_out = {
        str(month): {str(int(cluster_id)): round(float(share), 4) for cluster_id, share in row.items()}
        for month, row in monthly_topic_share.iterrows()
    }

    on_progress(steps["highlights"])
    rng = np.random.default_rng(42)
    monthly_sample = (
        conv_docs.groupby("start_month")["conversation_id"]
        .apply(lambda ids: rng.choice(ids.values))
        .sort_index()
        .tail(12)
    )
    highlights = []
    for month, conv_id in monthly_sample.items():
        rows = clean_df.loc[clean_df["conversation_id"] == conv_id].sort_values("timestamp")
        text = "\n".join(f"{row.role}: {row.text}" for row in rows.itertuples())[:1500]
        highlights.append({"month": month, "text": summarize_highlight(text, lang=lang)})

    on_progress(steps["done"])
    return {
        "overview": overview,
        "activity": activity,
        "language_ratio": language_ratio,
        "rewrite_rate": rewrite_rate,
        "clusters": cluster_info,
        "monthly_topic_share": monthly_topic_share_out,
        "highlights": highlights,
    }
