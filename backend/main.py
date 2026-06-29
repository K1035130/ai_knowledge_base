"""FastAPI app: drag-and-drop a ChatGPT export -> background job -> polished report JSON.

Run with: uvicorn backend.main:app --reload --port 8000
"""

import shutil
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.pipeline import build_report  # noqa: E402

app = FastAPI(title="AI Usage Report")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store. Single-user local app — no Redis/Celery needed.
_jobs: dict[str, dict] = {}


def _run_job(job_id: str, export_paths: list[Path], lang: str, tmp_dir: str) -> None:
    def on_progress(step: str) -> None:
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

    tmp_dir = tempfile.mkdtemp(prefix="ai_usage_report_")
    export_paths = []
    for file in files:
        dest = Path(tmp_dir) / file.filename
        dest.write_bytes(await file.read())
        export_paths.append(dest)

    job_id = str(uuid.uuid4())
    step_queued = "排队中" if lang == "zh" else "Queued"
    _jobs[job_id] = {"status": "running", "step": step_queued, "result": None, "error": None}
    background_tasks.add_task(_run_job, job_id, export_paths, lang, tmp_dir)

    return {"job_id": job_id}


@app.get("/api/reports/{job_id}")
async def get_report(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job
