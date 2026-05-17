import logging
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, FileResponse

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.schemas.analysis import AnalysisSummary, AnalysisResponse, LogResult
from backend.services import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _error(code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "code": code, "message": message},
    )


@router.get("", response_model=list[AnalysisSummary])
async def list_results(session: AsyncSession = Depends(get_session)):
    analyses = await storage_service.get_analyses(session)
    return [
        AnalysisSummary(
            analysis_id=a.id,
            source_type=a.source_type,
            source_name=a.source_name,
            analysis_mode=a.analysis_mode,
            generated_at=a.generated_at,
            total_logs=a.total_logs,
            malicious_count=a.malicious_count,
            suspicious_count=a.suspicious_count,
            benign_count=a.benign_count,
            avg_total_time_sec=a.avg_total_time_sec,
            csv_download_url=f"/api/results/{a.id}/download",
        )
        for a in analyses
    ]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_result(analysis_id: str, session: AsyncSession = Depends(get_session)):
    analysis = await storage_service.get_analysis_by_id(session, analysis_id)
    if not analysis:
        return _error("NOT_FOUND", f"Analysis {analysis_id} not found.", 404)

    log_rows = await storage_service.get_log_results(session, analysis_id)

    results = [
        LogResult(
            index=r.line_index,
            log=r.log_text,
            label=r.label,
            status=r.status,
            severity=r.severity,
            analysis_mode=r.analysis_mode,
            classification_time_sec=r.classification_time_sec,
            explanation_time_sec=r.explanation_time_sec,
            recommendation_time_sec=r.recommendation_time_sec,
            analysis_generation_time_sec=r.analysis_generation_time_sec,
            total_time_sec=r.total_time_sec,
            raw_classification=r.raw_classification or "",
            explanation=r.explanation or "",
            recommendation=r.recommendation or "",
            simulated_action=r.simulated_action,
        )
        for r in log_rows
    ]

    return AnalysisResponse(
        analysis_id=analysis.id,
        source_type=analysis.source_type,
        source_name=analysis.source_name,
        analysis_mode=analysis.analysis_mode,
        generated_at=analysis.generated_at,
        total_logs=analysis.total_logs,
        malicious_count=analysis.malicious_count,
        suspicious_count=analysis.suspicious_count,
        benign_count=analysis.benign_count,
        avg_classification_time_sec=analysis.avg_classification_time_sec,
        avg_analysis_generation_time_sec=analysis.avg_analysis_generation_time_sec,
        avg_total_time_sec=analysis.avg_total_time_sec,
        csv_download_url=f"/api/results/{analysis.id}/download",
        results=results,
    )


@router.get("/{analysis_id}/download")
async def download_csv(analysis_id: str, session: AsyncSession = Depends(get_session)):
    csv_path = await storage_service.get_csv_path(session, analysis_id)
    if not csv_path:
        return _error("NOT_FOUND", f"Analysis {analysis_id} not found.", 404)

    path = Path(csv_path)
    if not path.exists():
        return _error("NOT_FOUND", "CSV file not found on disk.", 404)

    return FileResponse(
        path=str(path),
        media_type="text/csv",
        filename=path.name,
    )
