"""
Job-based analysis endpoints.
POST /api/jobs/file   — upload file, get job_id immediately
POST /api/jobs/text   — paste text, get job_id immediately
GET  /api/jobs/{id}   — poll progress + partial results
POST /api/jobs/{id}/cancel — cancel running job
"""
import asyncio
import shutil
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.services.model_loader as ml
from backend.services import pipeline_service
from backend.services.job_service import create_job, get_job, cancel_job, run_job
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".log", ".csv"}


def _error(code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "code": code, "message": message},
    )


def _job_response(job):
    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total,
        "processed": job.processed,
        "analysis_mode": job.analysis_mode,
        "source_name": job.source_name,
        "results": job.results,
        "error": job.error,
        "analysis_id": job.analysis_id,
        "csv_download_url": job.csv_download_url,
        "avg_classification_time_sec": job.avg_classification_time_sec,
        "avg_analysis_generation_time_sec": job.avg_analysis_generation_time_sec,
        "avg_total_time_sec": job.avg_total_time_sec,
    }


# ── Start file analysis job ───────────────────────────────────────────────────

@router.post("/file")
async def start_file_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analysis_mode: str = Form("combined"),
):
    if not ml.model_loaded:
        return _error("MODEL_NOT_LOADED", ml.model_error or "Model is not available.", 503)

    if analysis_mode not in ("combined", "separate"):
        return _error("INVALID_ANALYSIS_MODE", "Use 'combined' or 'separate'.")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return _error("UNSUPPORTED_FILE_TYPE", "Only .txt, .log, and .csv files are supported.")

    upload_id = str(uuid.uuid4())[:8]
    dest = settings.uploads_dir_abs / f"{upload_id}_{file.filename}"
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        return _error("FILE_READ_ERROR", f"Could not save the uploaded file: {exc}")

    try:
        lines = pipeline_service.parse_uploaded_file(str(dest))
    except Exception as exc:
        return _error("FILE_READ_ERROR", f"Could not read file: {exc}")

    if not lines:
        return _error("EMPTY_FILE", "The uploaded file contains no log lines.")

    job = create_job(
        total=len(lines),
        source_name=file.filename or "upload",
        source_type="file",
        analysis_mode=analysis_mode,
    )
    background_tasks.add_task(run_job, job, lines)
    return {"job_id": job.id, "total": job.total}


# ── Start text analysis job ───────────────────────────────────────────────────

class TextJobRequest(BaseModel):
    text: str
    analysis_mode: str = "combined"


@router.post("/text")
async def start_text_job(
    body: TextJobRequest,
    background_tasks: BackgroundTasks,
):
    if not ml.model_loaded:
        return _error("MODEL_NOT_LOADED", ml.model_error or "Model is not available.", 503)

    if body.analysis_mode not in ("combined", "separate"):
        return _error("INVALID_ANALYSIS_MODE", "Use 'combined' or 'separate'.")

    if not body.text or not body.text.strip():
        return _error("EMPTY_TEXT", "The submitted text contains no log lines.")

    lines = pipeline_service.load_logs_from_text(body.text)
    if not lines:
        return _error("EMPTY_TEXT", "The submitted text contains no log lines.")

    job = create_job(
        total=len(lines),
        source_name="manual_input",
        source_type="text",
        analysis_mode=body.analysis_mode,
    )
    background_tasks.add_task(run_job, job, lines)
    return {"job_id": job.id, "total": job.total}


# ── Poll job progress ─────────────────────────────────────────────────────────

@router.get("/{job_id}")
async def poll_job(job_id: str):
    job = get_job(job_id)
    if not job:
        return _error("NOT_FOUND", f"Job {job_id} not found.", 404)
    return _job_response(job)


# ── Cancel job ────────────────────────────────────────────────────────────────

@router.post("/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str):
    job = get_job(job_id)
    if not job:
        return _error("NOT_FOUND", f"Job {job_id} not found.", 404)
    cancelled = cancel_job(job_id)
    return {"job_id": job_id, "cancelled": cancelled, "status": job.status}
