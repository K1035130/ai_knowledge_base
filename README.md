# AI Knowledge Base — Personal AI Usage Annual Report

A personal analytics web app that turns your ChatGPT conversation export into a Bilibili-style "annual report": when you used AI, what you talked about, and a few narrative highlights pulled from your own history — rendered as a paginated, animated story you flip through like a slideshow. Started as a hands-on ML learning project (EDA → embeddings → clustering → LLM labeling) and grew into a full FastAPI + React app.

## How it works

1. Drag and drop your ChatGPT export's `conversations.json` (or several) onto the upload page.
2. The backend parses, cleans, embeds, clusters, and asks Gemini to name the topic clusters and write monthly highlight blurbs — all in memory, nothing is written to disk and nothing is kept after the job finishes.
3. The frontend polls for progress and then renders the report as a 6-page animated story: overview → activity → habits → topics → highlights → done.

Everything is bilingual end-to-end (Chinese/English) — the language you pick on the upload page also controls what language Gemini writes in.

## Pipeline

| Stage | What it does | Module |
|---|---|---|
| 0. Parsing | Flattens the ChatGPT export's branching `mapping` tree (handles retried/regenerated messages) into a tidy table: `conversation_id, turn, role, timestamp, text` | `src/parsing/chatgpt_parser.py` |
| 1. Usage profile | Activity by hour/weekday/month, session/thread-span/response-time stats, language ratio, rewrite/regen rate | `src/analysis/usage_profile.py` |
| 2. Embedding + clustering | Encodes conversations with a multilingual sentence-transformer, picks k via the kneedle method on KMeans inertia, extracts topic keywords with c-TF-IDF | `src/embedding/encoder.py`, `src/clustering/topic_model.py` |
| 3. LLM labeling | Gemini names each topic cluster and writes a one-sentence highlight for a sampled conversation per month, in the user's chosen language | `src/llm/gemini_client.py` |
| 4. Report orchestration | Runs the full pipeline end-to-end and reports progress step-by-step | `backend/pipeline.py` |
| 5. API + job queue | FastAPI endpoints for upload (`POST /api/reports`) and polling (`GET /api/reports/{job_id}`), in-memory job store, background task execution | `backend/main.py` |
| 6. Web frontend | Vite + React + TypeScript app: iOS-style upload flow, animated paginated report, bubble-cloud topic chart, bilingual UI | `frontend/` |

## Project structure

```
ai_knowledge_base/
├── config.py                  # paths, model name, random seed
├── data/{raw,processed,embeddings}/   # gitignored — raw exports are personal data
├── src/{parsing,analysis,embedding,clustering,search,llm,utils}/
├── backend/                    # FastAPI app (pipeline.py, main.py)
├── frontend/                   # Vite + React + TS web app
├── app/streamlit_app.py        # early throwaway prototype, superseded by frontend/
├── notebooks/                  # interactive EDA / exploration
└── tests/
```

## Setup

Backend:

```bash
conda activate aikb
pip install -r requirements.txt
echo GEMINI_API_KEY=your_key_here > .env
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite dev server URL, drop your export file in, and pick a language before uploading (language is locked once processing starts).

## Embedding model: bilingual support matters here

Conversations with AI assistants are frequently Chinese text mixed with English technical terms or code, so the embedding model must understand both languages **and** align them semantically. We benchmarked two options by encoding short paired sentences and measuring cosine similarity:

| Test pair | `all-MiniLM-L6-v2` (English-only) | `paraphrase-multilingual-MiniLM-L12-v2` |
|---|---|---|
| Chinese synonymous sentences | 0.616 | 0.636 |
| Chinese unrelated sentences | 0.472 (barely separated from the synonymous pair above) | 0.046 (clearly separated) |
| Chinese vs. English, same meaning | 0.146 (treated as unrelated) | 0.708 (correctly recognized as similar) |

`all-MiniLM-L6-v2` was trained almost entirely on English and cannot tell related from unrelated Chinese sentences apart, let alone match Chinese and English paraphrases. **`config.py` is set to `paraphrase-multilingual-MiniLM-L12-v2`**, which separates related/unrelated pairs clearly and aligns Chinese-English paraphrases. This directly affects clustering quality (Stage 2) and report relevance, so don't swap it back to an English-only model without re-running this kind of check.

## Privacy

The upload page shows a bilingual notice before any file is accepted: conversation files are processed entirely in memory, never written to persistent storage, and never used for anything beyond generating the report for that one session.

## Status

- Parsing, usage profile, embedding/clustering, Gemini labeling, FastAPI backend, and the full React report UI are all built and validated against a real 741-conversation export.
- `tests/test_parsing.py` covers the parser; the rest of the pipeline has been sanity-checked by diffing backend output against the notebook's already-confirmed numbers.
- `notebooks/01_eda.ipynb` remains as the original exploratory workbench.

---

# AI 知识库 —— 个人 AI 使用年度报告

一个把 ChatGPT 对话导出文件加工成类似 Bilibili 年度报告的个人分析网页应用：你什么时候用的 AI、聊了什么主题，再从你自己的历史对话里摘出几条叙事性的高光时刻——做成可以像翻页故事一样逐页查看的动画报告。最初是一个边做边学的机器学习练习项目（EDA → embedding → 聚类 → LLM 命名），后来发展成了一套完整的 FastAPI + React 应用。

## 工作流程

1. 把 ChatGPT 导出的 `conversations.json`（可以是多个文件）拖拽到上传页面。
2. 后端在内存中完成解析、清洗、向量化、聚类，并请 Gemini 给话题簇命名、为每月写一条高光小结——全程不落盘，任务结束后也不会保留任何数据。
3. 前端轮询处理进度，完成后把报告渲染成6页动画式故事：总览 → 使用时间 → 使用习惯 → 话题 → 高光 → 结束。

整个应用从头到尾都是中英双语的——你在上传页选的语言，也决定了 Gemini 用什么语言生成内容。

## 处理流程

| 阶段 | 做什么 | 对应模块 |
|---|---|---|
| 0. 解析 | 把 ChatGPT 导出文件里带分支的 `mapping` 树结构（处理"重新生成"留下的分支）摊平成整洁表格：`conversation_id, turn, role, timestamp, text` | `src/parsing/chatgpt_parser.py` |
| 1. 使用画像 | 按小时/星期/月份统计活跃度、会话/对话线程跨度/响应时间统计、语言占比、改写/重新生成率 | `src/analysis/usage_profile.py` |
| 2. Embedding + 聚类 | 用多语言 sentence-transformer 编码对话，用 kneedle 方法在 KMeans inertia 曲线上选 k，再用 c-TF-IDF 提取主题关键词 | `src/embedding/encoder.py`、`src/clustering/topic_model.py` |
| 3. LLM 命名 | Gemini 给每个话题簇命名，并按用户选择的语言为每月抽样的一条对话写一句高光小结 | `src/llm/gemini_client.py` |
| 4. 报告编排 | 端到端跑完整个流程，逐步上报进度 | `backend/pipeline.py` |
| 5. API + 任务队列 | FastAPI 接口负责上传（`POST /api/reports`）和轮询（`GET /api/reports/{job_id}`），内存任务存储，后台异步执行 | `backend/main.py` |
| 6. 前端网页 | Vite + React + TypeScript 应用：iOS 风格上传流程、分页动画报告、气泡云话题图、中英双语界面 | `frontend/` |

## 项目结构

```
ai_knowledge_base/
├── config.py                  # 路径、模型名、随机种子
├── data/{raw,processed,embeddings}/   # 已 gitignore —— 原始导出是个人隐私数据
├── src/{parsing,analysis,embedding,clustering,search,llm,utils}/
├── backend/                    # FastAPI 应用（pipeline.py、main.py）
├── frontend/                   # Vite + React + TS 网页应用
├── app/streamlit_app.py        # 早期的一次性原型，已被 frontend/ 取代
├── notebooks/                  # 交互式 EDA / 探索分析
└── tests/
```

## 环境搭建

后端：

```bash
conda activate aikb
pip install -r requirements.txt
echo GEMINI_API_KEY=你的key > .env
uvicorn backend.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

打开 Vite 开发服务器给出的地址，拖入导出文件，记得在上传前先选好语言（处理开始后语言就锁定了）。

## Embedding 模型：双语支持很关键

和 AI 助手的对话经常是中文夹杂英文技术词汇或代码，所以 embedding 模型既要懂中文，**也要能把中英文对齐到同一语义空间**。我们对两个候选模型做了一组短句对的 cosine 相似度测试：

| 测试句对 | `all-MiniLM-L6-v2`（纯英文模型） | `paraphrase-multilingual-MiniLM-L12-v2` |
|---|---|---|
| 中文同义句 | 0.616 | 0.636 |
| 中文无关句 | 0.472（和上面的同义句几乎分不开） | 0.046（明显区分开） |
| 中文 vs 英文同义 | 0.146（被当作不相关） | 0.708（正确识别为相似） |

`all-MiniLM-L6-v2` 几乎完全是用英文语料训练的，连中文里"相关"和"无关"的句子都分不清，更别说对齐中英文同义句。**`config.py` 已经改成了 `paraphrase-multilingual-MiniLM-L12-v2`**，它能清楚区分中文相关/无关句对，也能正确对齐中英文同义表达。这直接影响阶段2的聚类质量和报告的相关性，所以不要在没有重新做类似验证的情况下换回纯英文模型。

## 隐私

上传页在接受任何文件之前会先展示中英双语的提示：对话文件全程只在内存中处理，不会写入持久化存储，也不会用于本次报告生成之外的任何目的。

## 当前进度

- 解析、使用画像、embedding/聚类、Gemini 命名、FastAPI 后端，以及完整的 React 报告界面都已经基于一份真实的 741 条对话导出文件构建并验证过。
- `tests/test_parsing.py` 覆盖了解析器；流程剩余部分通过对比后端输出和 notebook 里已验证过的数字做了一致性检查。
- `notebooks/01_eda.ipynb` 仍保留作为最初的探索性练习记录。
