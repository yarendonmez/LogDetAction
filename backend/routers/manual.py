import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.schemas.analysis import AnalysisResponse, TextAnalysisRequest
from backend.services import pipeline_service
import backend.services.model_loader as ml
from backend.routers._shared import run_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


def _error(code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "code": code, "message": message},
    )


@router.post("/text", response_model=AnalysisResponse)
async def analyze_text(
    body: TextAnalysisRequest,
    session: AsyncSession = Depends(get_session),
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

    try:
        response = await run_analysis(
            lines=lines,
            analysis_mode=body.analysis_mode,
            source_type="text",
            source_name="manual_input",
            session=session,
        )
    except Exception as exc:
        logger.exception("Analysis error: %s", exc)
        return _error("ANALYSIS_RUNTIME_ERROR", f"Analysis failed: {exc}", 500)

    return response
