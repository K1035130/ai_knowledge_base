# AI Knowledge Base — Personal AI Usage Report

A personal analytics project that turns your ChatGPT/Claude conversation exports into a Bilibili-style "annual usage report": when you use AI, what you talk about, and semantic search over your own history. Built as a hands-on ML learning project (EDA → embeddings → clustering → semantic search → dashboard).

## Pipeline

| Stage | What it does | Module |
|---|---|---|
| 0. Parsing | Flattens the ChatGPT export's branching `mapping` tree (handles retried/regenerated messages) into a tidy table: `conversation_id, turn, role, timestamp, text` | `src/parsing/chatgpt_parser.py` |
| 1. Usage profile (EDA) | Time-series features — activity by hour/weekday/month, conversation length distribution | `src/analysis/usage_profile.py` |
| 2. Embedding + clustering | Encodes conversations with sentence-transformers, clusters with KMeans (elbow method) or optionally BERTopic, extracts topic keywords with c-TF-IDF | `src/embedding/encoder.py`, `src/clustering/topic_model.py` |
| 3. Semantic search | Cosine similarity over cached embeddings to find related past conversations | `src/search/semantic_search.py` |
| 4. Dashboard | Streamlit app combining the usage profile and search | `app/streamlit_app.py` |

## Project structure

```
ai_knowledge_base/
├── config.py                  # paths, model name, random seed
├── data/{raw,processed,embeddings}/   # gitignored — raw exports are personal data
├── src/{parsing,analysis,embedding,clustering,search,utils}/
├── app/streamlit_app.py
├── notebooks/                 # interactive EDA/exploration
└── tests/
```

## Setup

```bash
conda activate aikb
pip install -r requirements.txt
```

Drop your ChatGPT export's `conversations.json` into `data/raw/`, then:

```bash
python -m src.parsing.chatgpt_parser
```

This writes `data/processed/conversations.parquet`.

## Embedding model: bilingual support matters here

Conversations with AI assistants are frequently Chinese text mixed with English technical terms or code, so the embedding model must understand both languages **and** align them semantically. We benchmarked two options by encoding short paired sentences and measuring cosine similarity:

| Test pair | `all-MiniLM-L6-v2` (English-only) | `paraphrase-multilingual-MiniLM-L12-v2` |
|---|---|---|
| Chinese synonymous sentences | 0.616 | 0.636 |
| Chinese unrelated sentences | 0.472 (barely separated from the synonymous pair above) | 0.046 (clearly separated) |
| Chinese vs. English, same meaning | 0.146 (treated as unrelated) | 0.708 (correctly recognized as similar) |

`all-MiniLM-L6-v2` was trained almost entirely on English and cannot tell related from unrelated Chinese sentences apart, let alone match Chinese and English paraphrases. **`config.py` is set to `paraphrase-multilingual-MiniLM-L12-v2`**, which separates related/unrelated pairs clearly and aligns Chinese-English paraphrases. This directly affects clustering quality (Stage 2) and search relevance (Stage 3), so don't swap it back to an English-only model without re-running this kind of check.

## Status

- Stage 0 (parsing) — done, covered by `tests/test_parsing.py`
- Stage 1 (EDA) — in progress, in `notebooks/01_eda.ipynb`, using synthetic data
- Stages 2-4 — not started

---

# AI 知识库 —— 个人 AI 使用年度报告

一个把 ChatGPT/Claude 对话导出文件，加工成类似 Bilibili 年度报告的个人分析项目：你什么时候用 AI、聊了什么主题、还能对自己的历史对话做语义搜索。同时也是一个边做边学的机器学习练习项目（EDA → embedding → 聚类 → 语义搜索 → 可视化看板）。

## 处理流程

| 阶段 | 做什么 | 对应模块 |
|---|---|---|
| 0. 解析 | 把 ChatGPT 导出文件里带分支的 `mapping` 树结构（处理"重新生成"留下的分支）摊平成整洁表格：`conversation_id, turn, role, timestamp, text` | `src/parsing/chatgpt_parser.py` |
| 1. 使用画像（EDA） | 时间序列特征——按小时/星期/月份统计活跃度、对话长度分布 | `src/analysis/usage_profile.py` |
| 2. Embedding + 聚类 | 用 sentence-transformers 编码对话，KMeans（配合 elbow method 选 k）或可选 BERTopic 聚类，用 c-TF-IDF 提取主题关键词 | `src/embedding/encoder.py`、`src/clustering/topic_model.py` |
| 3. 语义搜索 | 对缓存的向量算 cosine 相似度，找出相关的历史对话 | `src/search/semantic_search.py` |
| 4. 可视化看板 | 整合使用画像和搜索功能的 Streamlit 应用 | `app/streamlit_app.py` |

## 项目结构

```
ai_knowledge_base/
├── config.py                  # 路径、模型名、随机种子
├── data/{raw,processed,embeddings}/   # 已 gitignore —— 原始导出是个人隐私数据
├── src/{parsing,analysis,embedding,clustering,search,utils}/
├── app/streamlit_app.py
├── notebooks/                 # 交互式 EDA / 探索分析
└── tests/
```

## 环境搭建

```bash
conda activate aikb
pip install -r requirements.txt
```

把 ChatGPT 导出的 `conversations.json` 放进 `data/raw/`，然后跑：

```bash
python -m src.parsing.chatgpt_parser
```

会生成 `data/processed/conversations.parquet`。

## Embedding 模型：双语支持很关键

和 AI 助手的对话经常是中文夹杂英文技术词汇或代码，所以 embedding 模型既要懂中文，**也要能把中英文对齐到同一语义空间**。我们对两个候选模型做了一组短句对的 cosine 相似度测试：

| 测试句对 | `all-MiniLM-L6-v2`（纯英文模型） | `paraphrase-multilingual-MiniLM-L12-v2` |
|---|---|---|
| 中文同义句 | 0.616 | 0.636 |
| 中文无关句 | 0.472（和上面的同义句几乎分不开） | 0.046（明显区分开） |
| 中文 vs 英文同义 | 0.146（被当作不相关） | 0.708（正确识别为相似） |

`all-MiniLM-L6-v2` 几乎完全是用英文语料训练的，连中文里"相关"和"无关"的句子都分不清，更别说对齐中英文同义句。**`config.py` 已经改成了 `paraphrase-multilingual-MiniLM-L12-v2`**，它能清楚区分中文相关/无关句对，也能正确对齐中英文同义表达。这直接影响阶段2的聚类质量和阶段3的检索相关性，所以不要在没有重新做类似验证的情况下换回纯英文模型。

## 当前进度

- 阶段0（解析）—— 已完成，`tests/test_parsing.py` 覆盖
- 阶段1（EDA）—— 进行中，在 `notebooks/01_eda.ipynb` 里用合成数据练习
- 阶段2-4 —— 尚未开始
