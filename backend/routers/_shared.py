"""
Shared helper: run pipeline, persist, and return AnalysisResponse.
"""
from __future__ import annotations
import asyncio
import uuid
import statistics
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.analysis import AnalysisResponse, LogResult
from backend.services import pipeline_service, csv_service, storage_service
from backend.config import settings

logger = logging.getLogger(__name__)


async def run_analysis(
    *,
    lines: list[str],
    analysis_mode: str,
    source_type: str,
    source_name: str,
    session: AsyncSession,
) -> AnalysisResponse:

    analysis_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    # Blocking GPU inference — run in thread
    raw_results: list[dict] = await asyncio.to_thread(
        pipeline_service.analyze_logs, lines, analysis_mode
    )

    # Attach index
    for i, r in enumerate(raw_results):
        r["index"] = i

    # Counts
    malicious_count = sum(1 for r in raw_results if r["label"] == "malicious")
    suspicious_count = sum(1 for r in raw_results if r["label"] == "suspicious")
    benign_count = sum(1 for r in raw_results if r["label"] == "benign")

    avg_class = round(
        statistics.mean(r["classification_time_sec"] for r in raw_results), 3
    )
    avg_analysis = round(
        statistics.mean(r["analysis_generation_time_sec"] for r in raw_results), 3
    )
    avg_total = round(
        statistics.mean(r["total_time_sec"] for r in raw_results), 3
    )

    # CSV
    csv_path = csv_service.save_results_csv(raw_results, source_name, analysis_id)
    csv_download_url = f"/api/results/{analysis_id}/download"

    # DB — analysis row
    await storage_service.insert_analysis(
        session,
        {
            "id": analysis_id,
            "source_type": source_type,
            "source_name": source_name,
            "analysis_mode": analysis_mode,
            "generated_at": generated_at,
            "total_logs": len(raw_results),
            "malicious_count": malicious_count,
            "suspicious_count": suspicious_count,
            "benign_count": benign_count,
            "avg_classification_time_sec": avg_class,
            "avg_analysis_generation_time_sec": avg_analysis,
            "avg_total_time_sec": avg_total,
            "csv_path": str(csv_path),
            "status": "completed",
        },
    )

    # DB — per-log rows
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
        for r in raw_results
    ]
    await storage_service.insert_log_results(session, log_rows)

    results = [
        LogResult(
            index=r["index"],
            log=r["log"],
            label=r["label"],
            status=r["status"],
            severity=r["severity"],
            analysis_mode=r["analysis_mode"],
            classification_time_sec=r["classification_time_sec"],
            explanation_time_sec=r["explanation_time_sec"],
            recommendation_time_sec=r["recommendation_time_sec"],
            analysis_generation_time_sec=r["analysis_generation_time_sec"],
            total_time_sec=r["total_time_sec"],
            raw_classification=r.get("raw_classification", ""),
            explanation=r.get("explanation", ""),
            recommendation=r.get("recommendation", ""),
            simulated_action=r.get("simulated_action"),
        )
        for r in raw_results
    ]

    return AnalysisResponse(
        analysis_id=analysis_id,
        source_type=source_type,
        source_name=source_name,
        analysis_mode=analysis_mode,
        generated_at=generated_at,
        total_logs=len(results),
        malicious_count=malicious_count,
        suspicious_count=suspicious_count,
        benign_count=benign_count,
        avg_classification_time_sec=avg_class,
        avg_analysis_generation_time_sec=avg_analysis,
        avg_total_time_sec=avg_total,
        csv_download_url=csv_download_url,
        results=results,
    )
