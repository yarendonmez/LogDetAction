"""
Live log monitor service.

Polls LIVE_LOG_PATH every LIVE_POLL_INTERVAL_SEC.
Reads only newly appended lines (tracks offset).
Analyzes each new line via existing pipeline service.
Stores results in SQLite as a live analysis session.
Never modifies the watched file.
Never executes real security actions.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.schemas.analysis import SEVERITY_MAP, SIMULATED_ACTION_MAP

logger = logging.getLogger(__name__)

# ── In-memory state ───────────────────────────────────────────────────────────

_state: dict = {
    "running": False,
    "live_session_id": None,
    "live_log_path": str(settings.live_log_path_abs),
    "analysis_mode": settings.LIVE_DEFAULT_ANALYSIS_MODE,
    "last_offset": 0,
    "processed_lines": 0,
    "last_event_at": None,
    "last_error": None,
}

_task: Optional[asyncio.Task] = None


def get_state() -> dict:
    return dict(_state)


async def start_monitor(analysis_mode: str = "combined") -> dict:
    global _task

    if _state["running"]:
        return {"error": True, "code": "LIVE_ALREADY_RUNNING", "message": "Live monitor is already running."}

    session_id = str(uuid.uuid4())
    _state.update({
        "running": True,
        "live_session_id": session_id,
        "analysis_mode": analysis_mode,
        "last_offset": 0,
        "processed_lines": 0,
        "last_event_at": None,
        "last_error": None,
        "live_log_path": str(settings.live_log_path_abs),
    })

    # Create the live analysis row in DB
    await _ensure_live_analysis_row(session_id, analysis_mode)

    _task = asyncio.create_task(_monitor_loop(session_id, analysis_mode))
    logger.info("Live monitor started — session %s, mode=%s, file=%s",
                session_id, analysis_mode, _state["live_log_path"])
    return get_state()


async def stop_monitor() -> dict:
    global _task

    if not _state["running"]:
        return {"error": True, "code": "LIVE_NOT_RUNNING", "message": "Live monitor is not running."}

    _state["running"] = False

    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None

    # Update DB status
    session_id = _state.get("live_session_id")
    if session_id:
        await _update_live_analysis_status(session_id, "stopped")

    logger.info("Live monitor stopped — session %s", session_id)
    return get_state()


# ── Monitor loop ──────────────────────────────────────────────────────────────

async def _monitor_loop(session_id: str, analysis_mode: str) -> None:
    from backend.services import pipeline_service

    log_path = Path(_state["live_log_path"])

    while _state["running"]:
        try:
            if not log_path.exists():
                _state["last_error"] = f"File not found: {log_path}"
                await asyncio.sleep(settings.LIVE_POLL_INTERVAL_SEC)
                continue

            file_size = log_path.stat().st_size

            # Handle file truncation / rotation
            if file_size < _state["last_offset"]:
                logger.warning("Live log file truncated — resetting offset to 0")
                _state["last_offset"] = 0

            if file_size <= _state["last_offset"]:
                await asyncio.sleep(settings.LIVE_POLL_INTERVAL_SEC)
                continue

            # Read only new bytes
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(_state["last_offset"])
                new_content = f.read()
                _state["last_offset"] = f.tell()

            new_lines = [l.strip() for l in new_content.splitlines() if l.strip()]
            if not new_lines:
                await asyncio.sleep(settings.LIVE_POLL_INTERVAL_SEC)
                continue

            # Analyze each new line (blocking inference in thread)
            for line in new_lines:
                if not _state["running"]:
                    break
                try:
                    result = await asyncio.to_thread(
                        pipeline_service.analyze_single_log, line, analysis_mode
                    )
                    result["index"] = _state["processed_lines"]
                    _state["processed_lines"] += 1
                    _state["last_event_at"] = datetime.now(timezone.utc).isoformat()
                    _state["last_error"] = None

                    await _persist_live_result(session_id, result)
                    logger.debug("Live: processed line %d — %s", _state["processed_lines"], result["label"])

                except Exception as exc:
                    _state["last_error"] = str(exc)
                    logger.exception("Live analysis error: %s", exc)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            _state["last_error"] = str(exc)
            logger.exception("Live monitor loop error: %s", exc)

        await asyncio.sleep(settings.LIVE_POLL_INTERVAL_SEC)


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _ensure_live_analysis_row(session_id: str, analysis_mode: str) -> None:
    from backend.database import AsyncSessionLocal
    from backend.services.storage_service import insert_analysis

    now = datetime.now(timezone.utc).isoformat()
    async with AsyncSessionLocal() as session:
        await insert_analysis(session, {
            "id": session_id,
            "source_type": "live",
            "source_name": settings.LIVE_LOG_PATH,
            "analysis_mode": analysis_mode,
            "generated_at": now,
            "total_logs": 0,
            "malicious_count": 0,
            "suspicious_count": 0,
            "benign_count": 0,
            "avg_classification_time_sec": 0.0,
            "avg_analysis_generation_time_sec": 0.0,
            "avg_total_time_sec": 0.0,
            "csv_path": None,
            "status": "running",
        })


async def _persist_live_result(session_id: str, result: dict) -> None:
    from backend.database import AsyncSessionLocal
    from backend.services.storage_service import insert_log_results
    from backend.models.analysis import Analysis
    from sqlalchemy import select, update

    now = datetime.now(timezone.utc).isoformat()

    async with AsyncSessionLocal() as session:
        await insert_log_results(session, [{
            "analysis_id": session_id,
            "line_index": result["index"],
            "log_text": result["log"],
            "label": result["label"],
            "severity": result["severity"],
            "status": result["status"],
            "analysis_mode": result["analysis_mode"],
            "classification_time_sec": result["classification_time_sec"],
            "explanation_time_sec": result["explanation_time_sec"],
            "recommendation_time_sec": result["recommendation_time_sec"],
            "analysis_generation_time_sec": result["analysis_generation_time_sec"],
            "total_time_sec": result["total_time_sec"],
            "raw_classification": result.get("raw_classification", ""),
            "explanation": result.get("explanation", ""),
            "recommendation": result.get("recommendation", ""),
            "simulated_action": result.get("simulated_action"),
            "created_at": now,
        }])

        # Update aggregate counts in the parent analysis row
        processed = _state["processed_lines"]
        mal = sum(1 for r in [result] if r["label"] == "malicious")
        sus = sum(1 for r in [result] if r["label"] == "suspicious")
        ben = sum(1 for r in [result] if r["label"] == "benign")

        await session.execute(
            update(Analysis)
            .where(Analysis.id == session_id)
            .values(
                total_logs=processed,
                status="running",
            )
        )
        await session.commit()


async def _update_live_analysis_status(session_id: str, status: str) -> None:
    from backend.database import AsyncSessionLocal
    from backend.models.analysis import Analysis
    from sqlalchemy import update

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Analysis)
            .where(Analysis.id == session_id)
            .values(status=status, total_logs=_state["processed_lines"])
        )
        await session.commit()
