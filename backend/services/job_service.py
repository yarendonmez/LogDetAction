"""
In-memory job store for async, cancellable log analysis.

Each job processes one log at a time so cancellation takes effect
between entries (never mid-inference). Partial results are always
persisted to DB + CSV when the job finishes or is cancelled.
"""
from __future__ import annotations
import asyncio
import logging
import statistics
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.config import settings
from backend.schemas.analysis import SEVERITY_MAP, SIMULATED_ACTION_MAP

logger = logging.getLogger(__name__)

# ── Job state ─────────────────────────────────────────────────────────────────

@dataclass
class Job:
    id: str
    status: str          # running | completed | cancelled | failed
    total: int
    processed: int
    results: list        # list[dict] — grows as logs are processed
    cancel_event: threading.Event
    analysis_mode: str
    source_type: str
    source_name: str
    error: Optional[str] = None
    analysis_id: Optional[str] = None
    csv_download_url: Optional[str] = None
    # Populated after save
    avg_classification_time_sec: float = 0.0
    avg_analysis_generation_time_sec: float = 0.0
    avg_total_time_sec: float = 0.0


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def create_job(
    *,
    total: int,
    source_name: str,
    source_type: str,
    analysis_mode: str,
) -> Job:
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        status="running",
        total=total,
        processed=0,
        results=[],
        cancel_event=threading.Event(),
        analysis_mode=analysis_mode,
        source_type=source_type,
        source_name=source_name,
    )
    with _lock:
        _jobs[job_id] = job
    logger.info("Job created: %s (%d logs, mode=%s)", job_id, total, analysis_mode)
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def cancel_job(job_id: str) -> bool:
    job = _jobs.get(job_id)
    if job and job.status == "running":
        job.cancel_event.set()
        logger.info("Job cancel requested: %s", job_id)
        return True
    return False


# ── Background runner ─────────────────────────────────────────────────────────

async def run_job(job: Job, lines: list[str]) -> None:
    """
    Processes lines one-at-a-time in async context.
    Each GPU call is wrapped in asyncio.to_thread so the event loop stays free.
    Cancellation is checked between logs.
    Results are saved to DB + CSV regardless of outcome.
    """
    from backend.services import pipeline_service

    try:
        for i, line in enumerate(lines):
            if job.cancel_event.is_set():
                break

            result = await asyncio.to_thread(
                pipeline_service.analyze_single_log, line, job.analysis_mode
            )
            result["index"] = i
            job.results.append(result)
            job.processed = i + 1
            logger.debug("Job %s: processed %d/%d", job.id, job.processed, job.total)

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        logger.exception("Job %s failed: %s", job.id, exc)
    else:
        job.status = "cancelled" if job.cancel_event.is_set() else "completed"
        logger.info("Job %s finished with status: %s", job.id, job.status)

    # Always persist whatever we have
    if job.results:
        try:
            await _persist(job)
        except Exception as exc:
            logger.exception("Job %s persist failed: %s", job.id, exc)


async def _persist(job: Job) -> None:
    from backend.database import AsyncSessionLocal
    from backend.services import csv_service, storage_service

    analysis_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()
    results = job.results

    malicious = sum(1 for r in results if r["label"] == "malicious")
    suspicious = sum(1 for r in results if r["label"] == "suspicious")
    benign = sum(1 for r in results if r["label"] == "benign")

    avg_class = round(statistics.mean(r["classification_time_sec"] for r in results), 3)
    avg_analysis = round(statistics.mean(r["analysis_generation_time_sec"] for r in results), 3)
    avg_total = round(statistics.mean(r["total_time_sec"] for r in results), 3)

    csv_path = csv_service.save_results_csv(results, job.source_name, analysis_id)

    async with AsyncSessionLocal() as session:
        await storage_service.insert_analysis(
            session,
            {
                "id": analysis_id,
                "source_type": job.source_type,
                "source_name": job.source_name,
                "analysis_mode": job.analysis_mode,
                "generated_at": generated_at,
                "total_logs": len(results),
                "malicious_count": malicious,
                "suspicious_count": suspicious,
                "benign_count": benign,
                "avg_classification_time_sec": avg_class,
                "avg_analysis_generation_time_sec": avg_analysis,
                "avg_total_time_sec": avg_total,
                "csv_path": str(csv_path),
                "status": job.status,
            },
        )
        log_rows = [
            {
                "analysis_id": analysis_id,
                "line_index": r["index"],
                "log_text": r["log"],
                "label": r["label"],
                "severity": r["severity"],
                "status": r["status"],
                "analysis_mode": r["analysis_mode"],
                "classification_time_sec": r["classification_time_sec"],
                "explanation_time_sec": r["explanation_time_sec"],
                "recommendation_time_sec": r["recommendation_time_sec"],
                "analysis_generation_time_sec": r["analysis_generation_time_sec"],
                "total_time_sec": r["total_time_sec"],
                "raw_classification": r.get("raw_classification", ""),
                "explanation": r.get("explanation", ""),
                "recommendation": r.get("recommendation", ""),
                "simulated_action": r.get("simulated_action"),
                "created_at": generated_at,
            }
            for r in results
        ]
        await storage_service.insert_log_results(session, log_rows)

    job.analysis_id = analysis_id
    job.csv_download_url = f"/api/results/{analysis_id}/download"
    job.avg_classification_time_sec = avg_class
    job.avg_analysis_generation_time_sec = avg_analysis
    job.avg_total_time_sec = avg_total
    logger.info("Job %s persisted as analysis %s", job.id, analysis_id)
