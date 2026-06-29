"""FastAPI app: drag-and-drop a ChatGPT export -> background job -> polished report JSON.

Run with: uvicorn backend.main:app --reload --port 8000
"""

import os
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.pipeline import build_report  # noqa: E402
from src.parsing.chatgpt_parser import parse_exports  # noqa: E402
from src.utils.memlog import log_rss  # noqa: E402

# Render's free tier caps the backend at 512MB RAM. Past this many conversations, the pipeline's
# memory use (embedding + KMeans + jieba's dictionary load + TF-IDF) has reliably tipped over that
# limit mid-job, crashing the whole report instead of finishing it — so we reject oversized uploads
# up front rather than letting them fail expensively partway through. 448 conversations were
# confirmed to work in testing; kept a safety margin below that rather than capping right at it.
MAX_CONVERSATIONS = 350

app = FastAPI(title="AI Usage Report")

# FRONTEND_ORIGIN holds the deployed frontend's URL in production (comma-separated if there's more than one).
# localhost:5173 always stays allowed so local dev keeps working unmodified.
_extra_origins = [o.strip() for o in os.environ.get("FRONTEND_ORIGIN", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", *_extra_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store. Single-user local app — no Redis/Celery needed.
_jobs: dict[str, dict] = {}

# Completed jobs (with the full report payload) were never evicted, so memory usage grew with
# every report ever generated since the process started — swept opportunistically on each new
# upload instead of running a background timer, since this app only ever sees occasional traffic.
_JOB_TTL_SECONDS = 30 * 60


def _evict_stale_jobs() -> None:
    cutoff = time.monotonic() - _JOB_TTL_SECONDS
    stale_ids = [job_id for job_id, job in _jobs.items() if job["created_at"] < cutoff]
    for job_id in stale_ids:
        del _jobs[job_id]


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}


def _run_job(job_id: str, export_paths: list[Path], lang: str, tmp_dir: str) -> None:
    def on_progress(step: str) -> None:
        log_rss(f"[{job_id[:8]}] {step}")
        _jobs[job_id]["step"] = step

    try:
        result = build_report(export_paths, lang=lang, on_progress=on_progress)
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["result"] = result
    except Exception as exc:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(exc)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/api/reports")
async def create_report(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    lang: str = Form("zh"),
) -> dict:
    if not files:
        raise HTTPException(400, "No files uploaded")
    if lang not in ("zh", "en"):
        lang = "zh"

    _evict_stale_jobs()

    tmp_dir = tempfile.mkdtemp(prefix="ai_usage_report_")
    export_paths = []
    for file in files:
        dest = Path(tmp_dir) / file.filename
        dest.write_bytes(await file.read())
        export_paths.append(dest)

    conversation_count = parse_exports(export_paths)["conversation_id"].nunique()
    if conversation_count > MAX_CONVERSATIONS:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if lang == "en":
            detail = (
                f"This upload has {conversation_count} conversations, more than this service can "
                f"reliably process right now (limit: {MAX_CONVERSATIONS}). Please upload fewer files "
                "and try again — if your export is split into numbered files, prefer keeping the "
                "higher-numbered ones."
            )
        else:
            detail = (
                f"这次上传包含 {conversation_count} 条对话，超出了当前服务能稳定处理的上限"
                f"（{MAX_CONVERSATIONS} 条）。请减少上传的文件数量后重试，"
                "如果导出文件是带编号的多个文件，尽量保留编号更大的文件。"
            )
        raise HTTPException(400, detail)

    job_id = str(uuid.uuid4())
    step_queued = "排队中" if lang == "zh" else "Queued"
    _jobs[job_id] = {
        "status": "running",
        "step": step_queued,
        "result": None,
        "error": None,
        "created_at": time.monotonic(),
    }
    background_tasks.add_task(_run_job, job_id, export_paths, lang, tmp_dir)

    return {"job_id": job_id}


@app.get("/api/reports/{job_id}")
async def get_report(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job
