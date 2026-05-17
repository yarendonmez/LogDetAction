import shutil
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_session
from backend.schemas.analysis import AnalysisResponse, ErrorResponse
from backend.services import pipeline_service
import backend.services.model_loader as ml
from backend.routers._shared import run_analysis

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".log", ".csv"}


def _error(code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "code": code, "message": message},
    )


@router.post("/file", response_model=AnalysisResponse)
async def analyze_file(
    file: UploadFile = File(...),
    analysis_mode: str = Form("combined"),
    session: AsyncSession = Depends(get_session),
):
    if not ml.model_loaded:
        return _error("MODEL_NOT_LOADED", ml.model_error or "Model is not available.", 503)

    if analysis_mode not in ("combined", "separate"):
        return _error("INVALID_ANALYSIS_MODE", "Use 'combined' or 'separate'.")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return _error(
            "UNSUPPORTED_FILE_TYPE",
            "Only .txt, .log, and .csv files are supported.",
        )

    # Save upload
    upload_id = str(uuid.uuid4())[:8]
    dest = settings.uploads_dir_abs / f"{upload_id}_{file.filename}"
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.exception("File save error: %s", exc)
        return _error("FILE_READ_ERROR", "Could not save the uploaded file.")

    # Parse lines
    try:
        lines = pipeline_service.parse_uploaded_file(str(dest))
    except Exception as exc:
        logger.exception("File parse error: %s", exc)
        return _error("FILE_READ_ERROR", f"Could not read file: {exc}")

    if not lines:
        return _error("EMPTY_FILE", "The uploaded file contains no log lines.")

    # Run pipeline
    try:
        response = await run_analysis(
            lines=lines,
            analysis_mode=analysis_mode,
            source_type="file",
            source_name=file.filename or "upload",
            session=session,
        )
    except Exception as exc:
        logger.exception("Analysis error: %s", exc)
        return _error("ANALYSIS_RUNTIME_ERROR", f"Analysis failed: {exc}", 500)

    return response
