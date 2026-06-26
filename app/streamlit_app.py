import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np
import streamlit as st

from config import EMBEDDING_DIR, PROCESSED_DIR
from src.analysis.usage_profile import activity_by_hour, activity_by_weekday, add_time_features
from src.search.semantic_search import search
from src.utils.io import load_parquet

st.set_page_config(page_title="AI 使用年度报告", layout="wide")
st.title("我的 AI 使用年度报告")

data_path = PROCESSED_DIR / "conversations.parquet"
embedding_path = EMBEDDING_DIR / "conversations.npy"

if not data_path.exists():
    st.warning("还没有处理好的数据，先运行 `python -m src.parsing.chatgpt_parser <export_path>`")
    st.stop()

df = add_time_features(load_parquet(data_path))

st.header("使用概览")
col1, col2 = st.columns(2)
col1.metric("总对话数", df["conversation_id"].nunique())
col2.metric("总消息数", len(df))

st.subheader("按小时活跃度")
st.bar_chart(activity_by_hour(df))

st.subheader("按星期活跃度")
st.bar_chart(activity_by_weekday(df))

st.header("语义搜索")
query = st.text_input("搜索你以前问过的内容")
if query:
    if not embedding_path.exists():
        st.warning("还没有生成 embedding 缓存，先运行 embedding 编码脚本")
    else:
        corpus_vecs = np.load(embedding_path)
        results = search(query, df, corpus_vecs, top_k=5)
        for _, row in results.iterrows():
            st.write(f"**[{row['role']}]** ({row['score']:.2f}) {row['text'][:200]}")
