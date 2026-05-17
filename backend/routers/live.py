"""
Live monitor endpoints.

POST /api/live/start
POST /api/live/stop
GET  /api/live/status
GET  /api/live/events
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import backend.services.model_loader as ml
from backend.database import get_session
from backend.services import live_monitor_service
from backend.services.storage_service import get_live_events

logger = logging.getLogger(__name__)
router = APIRouter()


def _error(code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "code": code, "message": message},
    )


class StartRequest(BaseModel):
    analysis_mode: str = "combined"


@router.post("/start")
async def start_live(body: StartRequest):
    if not ml.model_loaded:
        return _error("MODEL_NOT_LOADED", ml.model_error or "Model is not available.", 503)

    if body.analysis_mode not in ("combined", "separate"):
        return _error("INVALID_ANALYSIS_MODE", "Use 'combined' or 'separate'.")

    result = await live_monitor_service.start_monitor(body.analysis_mode)
    if isinstance(result, dict) and result.get("error"):
        return _error(result["code"], result["message"])
    return result


@router.post("/stop")
async def stop_live():
    result = await live_monitor_service.stop_monitor()
    if isinstance(result, dict) and result.get("error"):
        return _error(result["code"], result["message"])
    return result


@router.get("/status")
async def live_status():
    return live_monitor_service.get_state()


@router.get("/events")
async def live_events(
    limit: int = Query(50, ge=1, le=200),
    label: str = Query("all"),
    session: AsyncSession = Depends(get_session),
):
    state = live_monitor_service.get_state()
    session_id = state.get("live_session_id")
    if not session_id:
        return []

    rows = await get_live_events(session, session_id, limit=limit, label=label)
    return [
        {
            "index": r.line_index,
            "log": r.log_text,
            "label": r.label,
            "severity": r.severity,
            "status": r.status,
            "analysis_mode": r.analysis_mode,
            "classification_time_sec": r.classification_time_sec,
            "explanation_time_sec": r.explanation_time_sec,
            "recommendation_time_sec": r.recommendation_time_sec,
            "analysis_generation_time_sec": r.analysis_generation_time_sec,
            "total_time_sec": r.total_time_sec,
            "explanation": r.explanation or "",
            "recommendation": r.recommendation or "",
            "simulated_action": r.simulated_action,
            "created_at": r.created_at,
        }
        for r in reversed(rows)  # oldest first for table display
    ]
