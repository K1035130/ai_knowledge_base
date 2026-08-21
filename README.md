# AI Knowledge Base : Personal AI Usage Annual Report

A personal analytics web app that turns your ChatGPT conversation export into a Bilibili-style "annual report": when you used AI, what you talked about, and a few narrative highlights pulled from your own history : rendered as a paginated, animated story you flip through like a slideshow. Started as a hands-on ML learning project (EDA → embeddings → clustering → LLM labeling) and grew into a full FastAPI + React app.

**Try it here: https://ai-personal-report.onrender.com/** : this is the entry point to use.

Also live on AWS at https://d2lwi9nb2rcmz1.cloudfront.net, which serves the same frontend from S3/CloudFront. Both front ends now talk to the same backend on Render, so either works : the Render one is preferred simply because it is the deployment that is actually being maintained.

No export of your own handy? Both entry points have a **"See a sample report"** link under the upload box that opens a pre-generated report, so you can see the whole thing without uploading anything.

## How it works

1. Drag and drop your ChatGPT export's `conversations.json` (or several) onto the upload page.
2. The backend parses, cleans, embeds, clusters, and asks an LLM to name the topic clusters and write monthly highlight blurbs : all in memory, nothing is written to disk and nothing is kept after the job finishes.
3. The frontend polls for progress and then renders the report as a 6-page animated story: overview → activity → habits → topics → highlights → done.

Everything is bilingual end-to-end (Chinese/English) : the language you pick on the upload page also controls what language the LLM writes in.

## Pipeline

| Stage | What it does | Module |
|---|---|---|
| 0. Parsing | Flattens the ChatGPT export's branching `mapping` tree (handles retried/regenerated messages) into a tidy table: `conversation_id, turn, role, timestamp, text` | `src/parsing/chatgpt_parser.py` |
| 1. Usage profile | Activity by hour/weekday/month, session/thread-span/response-time stats, language ratio, rewrite/regen rate | `src/analysis/usage_profile.py` |
| 2. Embedding + clustering | Embeds conversations via SiliconFlow's embedding API (`BAAI/bge-m3`, 1024-d), picks k via the kneedle method on KMeans inertia, extracts topic keywords with TF-IDF | `src/embedding/encoder.py`, `src/clustering/topic_model.py` |
| 3. LLM labeling | An LLM (`Qwen/Qwen3-8B` on SiliconFlow) names each topic cluster and writes a one-sentence highlight for a sampled conversation per month, in the user's chosen language | `src/llm/siliconflow_client.py` |
| 4. Report orchestration | Runs the full pipeline end-to-end and reports progress step-by-step | `backend/pipeline.py` |
| 5. API + job queue | FastAPI endpoints for upload (`POST /api/reports`) and polling (`GET /api/reports/{job_id}`), in-memory job store, background task execution | `backend/main.py` |
| 6. Web frontend | Vite + React + TypeScript app: iOS-style upload flow, animated paginated report, bubble-cloud topic chart, bilingual UI | `frontend/` |

## Project structure

```
ai_knowledge_base/
├── config.py                  # paths, model name, random seed
├── data/{raw,processed,embeddings}/   # gitignored : raw exports are personal data
├── src/{parsing,analysis,embedding,clustering,search,llm,utils}/
├── backend/                    # FastAPI app (pipeline.py, main.py)
├── frontend/                   # Vite + React + TS web app
├── app/streamlit_app.py        # early throwaway prototype, superseded by frontend/
├── notebooks/                  # interactive EDA / exploration
├── render.yaml                 # Render Blueprint: backend web service + frontend static site
├── runtime.txt                 # pins the Python version Render builds with
├── requirements-render.txt     # minimal deps actually imported by backend/ : what Render installs
└── tests/
```

## Setup

Backend:

```bash
conda activate aikb
pip install -r requirements.txt
echo SILICONFLOW_API_KEY=your_key_here > .env
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

Conversations with AI assistants are frequently Chinese text mixed with English technical terms or code, so whatever embeds them must understand both languages **and** align them semantically. We originally benchmarked two local sentence-transformer options by encoding short paired sentences and measuring cosine similarity:

| Test pair | `all-MiniLM-L6-v2` (English-only) | `paraphrase-multilingual-MiniLM-L12-v2` |
|---|---|---|
| Chinese synonymous sentences | 0.616 | 0.636 |
| Chinese unrelated sentences | 0.472 (barely separated from the synonymous pair above) | 0.046 (clearly separated) |
| Chinese vs. English, same meaning | 0.146 (treated as unrelated) | 0.708 (correctly recognized as similar) |

`all-MiniLM-L6-v2` was trained almost entirely on English and cannot tell related from unrelated Chinese sentences apart, let alone match Chinese and English paraphrases. `paraphrase-multilingual-MiniLM-L12-v2` clearly separated related/unrelated pairs and aligned Chinese-English paraphrases, so it was the one wired into `config.py`.

**This local model was later replaced by Gemini's embedding API (`gemini-embedding-001`).** Not for quality reasons : its weights alone (~470MB in fp32) left no headroom in Render's 512MB free-tier memory limit, and crashed the backend with an out-of-memory restart the moment a real report tried to embed conversations. Calling Gemini's embedding API instead removes any local model from the running process entirely (the same client is already used for cluster naming and highlights), fixing the memory problem at the root rather than trimming it. A quick re-check confirms the swap didn't regress cross-lingual alignment: a Chinese sentence and its English paraphrase score 0.86 cosine similarity, while two unrelated Chinese sentences score only 0.59 : clearly separated, same direction as the table above.

**Then Gemini's access policy changed, and the provider moved once more : to SiliconFlow's `BAAI/bge-m3` (1024-d).** SiliconFlow speaks the OpenAI-compatible protocol, so `src/llm/siliconflow_client.py` is just the official `openai` SDK pointed at a different `base_url` : swapping provider again is a `base_url` + model-name change in `config.py`, not a rewrite. The vectors are now 1024-d instead of the 768 previously requested from `gemini-embedding-001`, which changes nothing downstream (KMeans and the cosine search are both dimension-agnostic, and no embeddings are cached on disk). One thing to watch: bge-m3 caps input at 8192 tokens and rejects anything longer with a 400, so `encoder.py` truncates each conversation doc to 6000 characters before sending. Same cross-lingual check re-run on the new model : Chinese synonymous sentences 0.927, Chinese vs. English paraphrase 0.900, two unrelated Chinese sentences 0.386 : a wider margin than either earlier setup.

This directly affects clustering quality (Stage 2) and report relevance, so don't swap the embedding model or provider again without re-running this kind of check.

## Deployment

**The backend runs on Render.** It used to run on an EC2 t3.micro behind CloudFront; that instance was terminated on 2026-08-21 and the whole thing moved to Render for cost reasons. A t3.micro plus its EBS volume costs real money every month whether or not anyone visits, and for a personal project that sits idle most of the time that was the single largest line item. Render's free tier costs nothing at idle, and it also removed the EC2-specific operational overhead entirely : no nginx to configure, no systemd unit, no SSH, and no public-DNS churn on every stop/start.

There are two front ends, both pointing at that one backend:

```
https://ai-personal-report.onrender.com     (preferred)
    static site on Render
    /api/*  → called directly, cross-origin (CORS allow-lists this origin)

https://d2lwi9nb2rcmz1.cloudfront.net       (still live)
    /*      → S3 bucket (static frontend)
    /api/*  → CloudFront origin → ai-report-backend-d7vs.onrender.com
```

- **Backend** (`ai-report-backend-d7vs.onrender.com`): Render web service, free tier, built from `requirements-render.txt`. `SILICONFLOW_API_KEY` and `FRONTEND_ORIGIN` are set in the Render dashboard (`sync: false` in `render.yaml`, so they are never committed). Deploys automatically on push to `main`.
- **Render frontend**: static site, built with `VITE_API_BASE_URL` pointing straight at the backend. Because that is a different origin, uploads depend on the backend's `FRONTEND_ORIGIN` CORS allow-list.
- **CloudFront frontend**: built with `VITE_API_BASE_URL=https://d2lwi9nb2rcmz1.cloudfront.net`, so the browser sees `/api/*` as same-origin and CORS never comes into play. CloudFront's `/api/*` behavior forwards to Render with the `Managed-AllViewerExceptHostHeader` origin request policy : this part is load-bearing. Render routes by `Host` header, so forwarding the viewer's `Host` (i.e. the CloudFront domain) would make Render's router return an empty 404 for every API call.

**The free tier spins down after about 15 minutes of inactivity.** The first request after that waits on a cold start, which can exceed CloudFront's 60s origin read timeout and surface as a 504 : retrying once works. The sample-report link is a static JSON file, so it always opens regardless of whether the backend is awake.

**Updating after a code change:**

Backend and Render frontend: just `git push` : Render rebuilds both.

CloudFront frontend:
```bash
cd frontend
VITE_API_BASE_URL=https://d2lwi9nb2rcmz1.cloudfront.net npm run build
aws s3 sync dist/ s3://ai-report-frontend-690167396475 --delete
aws cloudfront create-invalidation --distribution-id E1JY8ZIWY8GN4W --paths "/*"
```

The old `deploy/aws-sleep.ps1` / `deploy/aws-wake.ps1` hibernation scripts were deleted along with the instance : `aws-wake.ps1` repointed CloudFront's `/api/*` origin back at EC2, which would now break the API. The terminated instance's root volume survives as snapshot `snap-0dc0e51a8745eb693` (nginx + systemd config), in case that setup is ever needed again.

## Privacy

The upload page shows a bilingual notice before any file is accepted: conversation files are processed entirely in memory, never written to persistent storage, and never used for anything beyond generating the report for that one session.

## Status

- Parsing, usage profile, embedding/clustering, LLM labeling, FastAPI backend, and the full React report UI are all built and validated against a real 741-conversation export.
- `tests/test_parsing.py` covers the parser; the rest of the pipeline has been sanity-checked by diffing backend output against the notebook's already-confirmed numbers.
- Deployed and live: backend on Render, frontend served both from Render and from S3/CloudFront : see Deployment above.
- `notebooks/01_eda.ipynb` remains as the original exploratory workbench.

---

# AI 知识库 :: 个人 AI 使用年度报告

**在线体验入口：https://ai-personal-report.onrender.com/** ::想试用请优先从这里进。

AWS 上的 https://d2lwi9nb2rcmz1.cloudfront.net 也还活着，跑的是同一份前端（托管在 S3/CloudFront）。两个前端现在连的是同一个 Render 后端，所以哪个都能用::之所以推荐 Render 那个，只是因为它才是持续在维护的那套部署。

手边没有自己的导出文件？两个入口的上传框下面都有一个 **"看一份示例报告"** 的链接，点开就是一份预先生成好的完整报告，不用上传任何东西也能看到全貌。

一个把 ChatGPT 对话导出文件加工成类似 Bilibili 年度报告的个人分析网页应用：你什么时候用的 AI、聊了什么主题，再从你自己的历史对话里摘出几条叙事性的高光时刻::做成可以像翻页故事一样逐页查看的动画报告。最初是一个边做边学的机器学习练习项目（EDA → embedding → 聚类 → LLM 命名），后来发展成了一套完整的 FastAPI + React 应用。

## 工作流程

1. 把 ChatGPT 导出的 `conversations.json`（可以是多个文件）拖拽到上传页面。
2. 后端在内存中完成解析、清洗、向量化、聚类，并请大模型给话题簇命名、为每月写一条高光小结::全程不落盘，任务结束后也不会保留任何数据。
3. 前端轮询处理进度，完成后把报告渲染成6页动画式故事：总览 → 使用时间 → 使用习惯 → 话题 → 高光 → 结束。

整个应用从头到尾都是中英双语的::你在上传页选的语言，也决定了大模型用什么语言生成内容。

## 处理流程

| 阶段 | 做什么 | 对应模块 |
|---|---|---|
| 0. 解析 | 把 ChatGPT 导出文件里带分支的 `mapping` 树结构（处理"重新生成"留下的分支）摊平成整洁表格：`conversation_id, turn, role, timestamp, text` | `src/parsing/chatgpt_parser.py` |
| 1. 使用画像 | 按小时/星期/月份统计活跃度、会话/对话线程跨度/响应时间统计、语言占比、改写/重新生成率 | `src/analysis/usage_profile.py` |
| 2. Embedding + 聚类 | 调用硅基流动的 embedding API（`BAAI/bge-m3`，1024 维）编码对话，用 kneedle 方法在 KMeans inertia 曲线上选 k，再用 TF-IDF 提取主题关键词 | `src/embedding/encoder.py`、`src/clustering/topic_model.py` |
| 3. LLM 命名 | 大模型（硅基流动上的 `Qwen/Qwen3-8B`）给每个话题簇命名，并按用户选择的语言为每月抽样的一条对话写一句高光小结 | `src/llm/siliconflow_client.py` |
| 4. 报告编排 | 端到端跑完整个流程，逐步上报进度 | `backend/pipeline.py` |
| 5. API + 任务队列 | FastAPI 接口负责上传（`POST /api/reports`）和轮询（`GET /api/reports/{job_id}`），内存任务存储，后台异步执行 | `backend/main.py` |
| 6. 前端网页 | Vite + React + TypeScript 应用：iOS 风格上传流程、分页动画报告、气泡云话题图、中英双语界面 | `frontend/` |

## 项目结构

```
ai_knowledge_base/
├── config.py                  # 路径、模型名、随机种子
├── data/{raw,processed,embeddings}/   # 已 gitignore :: 原始导出是个人隐私数据
├── src/{parsing,analysis,embedding,clustering,search,llm,utils}/
├── backend/                    # FastAPI 应用（pipeline.py、main.py）
├── frontend/                   # Vite + React + TS 网页应用
├── app/streamlit_app.py        # 早期的一次性原型，已被 frontend/ 取代
├── notebooks/                  # 交互式 EDA / 探索分析
├── render.yaml                 # Render 部署蓝图：后端 Web Service + 前端 Static Site
├── runtime.txt                 # 固定 Render 构建用的 Python 版本
├── requirements-render.txt     # 后端真实会用到的精简依赖::Render 构建时装的就是这份
└── tests/
```

## 环境搭建

后端：

```bash
conda activate aikb
pip install -r requirements.txt
echo SILICONFLOW_API_KEY=你的key > .env
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

和 AI 助手的对话经常是中文夹杂英文技术词汇或代码，所以负责编码的模型既要懂中文，**也要能把中英文对齐到同一语义空间**。我们最初对两个本地 sentence-transformer 候选模型做了一组短句对的 cosine 相似度测试：

| 测试句对 | `all-MiniLM-L6-v2`（纯英文模型） | `paraphrase-multilingual-MiniLM-L12-v2` |
|---|---|---|
| 中文同义句 | 0.616 | 0.636 |
| 中文无关句 | 0.472（和上面的同义句几乎分不开） | 0.046（明显区分开） |
| 中文 vs 英文同义 | 0.146（被当作不相关） | 0.708（正确识别为相似） |

`all-MiniLM-L6-v2` 几乎完全是用英文语料训练的，连中文里"相关"和"无关"的句子都分不清，更别说对齐中英文同义句。`paraphrase-multilingual-MiniLM-L12-v2` 能清楚区分中文相关/无关句对，也能正确对齐中英文同义表达，所以当时把它配进了 `config.py`。

**后来这个本地模型被换成了 Gemini 的 embedding API（`gemini-embedding-001`）。** 原因不是效果问题::它的模型权重本身（fp32 下约470MB）几乎把 Render 免费版 512MB 的内存配额占满，一旦真的有报告任务要做 embedding，后端就会因为内存溢出被强制重启。改成调用 Gemini 的 embedding API 之后，运行中的进程里完全不再加载任何本地模型（复用的还是给话题命名、写高光小结用的同一个 client），是从根上解决内存问题，而不是单纯把占用压小。换模型后做了一次同样的验证：一句中文和它的英文同义句 cosine 相似度 0.86，而两句不相关的中文句子只有 0.59::区分得很清楚，跟上面那张表里多语言模型的结论方向一致。

**再后来 Gemini 的使用政策变了，服务商又换了一次::改成硅基流动的 `BAAI/bge-m3`（1024 维）。** 硅基流动走的是 OpenAI 兼容协议，所以 `src/llm/siliconflow_client.py` 其实就是官方 `openai` SDK 换了个 `base_url`::以后再换服务商，改的是 `config.py` 里的 `base_url` 和模型名，不用重写客户端。向量维度从原来向 `gemini-embedding-001` 要的 768 维变成 1024 维，对下游没有任何影响（KMeans 和余弦检索都不关心维度，磁盘上也没有缓存过 embedding）。有一点要注意：bge-m3 单条输入上限是 8192 token，超了会直接返回 400，所以 `encoder.py` 在发送前把每条对话文档截断到 6000 字符。换模型后又跑了一遍同样的验证：中文同义句 0.927，中英文同义句 0.900，两句不相关的中文 0.386::区分度比前面两套方案都更好。

这直接影响阶段2的聚类质量和报告的相关性，所以不要在没有重新做类似验证的情况下，再换别的 embedding 模型或服务商。

## 部署

**后端跑在 Render 上。** 原本是跑在 CloudFront 后面的一台 EC2 t3.micro，那台实例已于 2026-08-21 终止，整套迁到了 Render，**原因是成本**：t3.micro 加上它的 EBS 卷，不管有没有人访问都要按月实打实地付钱，而这种大部分时间闲置的个人项目，这就是最大的一笔开销。Render 免费版闲置时不产生费用，顺带还把 EC2 那套运维负担整个消掉了::不用配 nginx、不用写 systemd unit、不用 SSH，也不用再应付每次 stop/start 公网 DNS 都会变的问题。

现在有两个前端，连的是同一个后端：

```
https://ai-personal-report.onrender.com     （推荐入口）
    Render 上的静态站点
    /api/*  → 直接跨域调用后端（CORS 白名单里有这个域名）

https://d2lwi9nb2rcmz1.cloudfront.net       （仍然可用）
    /*      → S3 bucket（静态前端）
    /api/*  → CloudFront origin → ai-report-backend-d7vs.onrender.com
```

- **后端**（`ai-report-backend-d7vs.onrender.com`）：Render Web Service，免费版，按 `requirements-render.txt` 构建。`SILICONFLOW_API_KEY` 和 `FRONTEND_ORIGIN` 在 Render 控制台里设置（`render.yaml` 里是 `sync: false`，所以永远不会被提交进仓库）。推送到 `main` 会自动部署。
- **Render 前端**：静态站点，构建时 `VITE_API_BASE_URL` 直接指向后端。因为这是跨域调用，所以上传功能依赖后端 `FRONTEND_ORIGIN` 里的 CORS 白名单。
- **CloudFront 前端**：以 `VITE_API_BASE_URL=https://d2lwi9nb2rcmz1.cloudfront.net` 构建，因此浏览器看到的 `/api/*` 是同源请求，压根不会触发 CORS。CloudFront 的 `/api/*` 行为用 `Managed-AllViewerExceptHostHeader` 这条 origin request policy 转发到 Render::**这一条是关键**。Render 靠 `Host` 头决定路由，如果把访客的 `Host`（也就是 CloudFront 域名）原样转发过去，Render 的路由器会对每个 API 请求返回一个空的 404。

**免费版闲置约 15 分钟后会 spin down。** 之后的第一个请求要等冷启动，可能超过 CloudFront 60 秒的 origin 读取超时而表现为 504::重试一次即可。示例报告是个静态 JSON 文件，所以不管后端醒着还是睡着都能打开。

**更新代码后的部署流程：**

后端和 Render 前端：直接 `git push` 就行::Render 会自动重新构建这两个。

CloudFront 前端：
```bash
cd frontend
VITE_API_BASE_URL=https://d2lwi9nb2rcmz1.cloudfront.net npm run build
aws s3 sync dist/ s3://ai-report-frontend-690167396475 --delete
aws cloudfront create-invalidation --distribution-id E1JY8ZIWY8GN4W --paths "/*"
```

原来的 `deploy/aws-sleep.ps1` / `deploy/aws-wake.ps1` 休眠脚本已经随实例一起删除::`aws-wake.ps1` 的作用是把 CloudFront 的 `/api/*` origin 指回 EC2，现在再跑一次只会把 API 弄挂。那台实例的根卷保留成了快照 `snap-0dc0e51a8745eb693`（含 nginx 和 systemd 配置），万一以后还需要那套环境可以从它恢复。

## 隐私

上传页在接受任何文件之前会先展示中英双语的提示：对话文件全程只在内存中处理，不会写入持久化存储，也不会用于本次报告生成之外的任何目的。

## 当前进度

- 解析、使用画像、embedding/聚类、大模型命名、FastAPI 后端，以及完整的 React 报告界面都已经基于一份真实的 741 条对话导出文件构建并验证过。
- `tests/test_parsing.py` 覆盖了解析器；流程剩余部分通过对比后端输出和 notebook 里已验证过的数字做了一致性检查。
- 已经部署上线：后端在 Render，前端同时由 Render 和 S3/CloudFront 提供::见上面的"部署"一节。
- `notebooks/01_eda.ipynb` 仍保留作为最初的探索性练习记录。
