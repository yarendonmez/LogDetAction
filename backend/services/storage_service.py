"""
SQLite persistence via async SQLAlchemy.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.analysis import Analysis, LogResult

logger = logging.getLogger(__name__)


# ── Write ─────────────────────────────────────────────────────────────────────

async def insert_analysis(session: AsyncSession, data: dict) -> None:
    row = Analysis(**data)
    session.add(row)
    await session.commit()


async def insert_log_results(session: AsyncSession, rows: list[dict]) -> None:
    for row_data in rows:
        row = LogResult(**row_data)
        session.add(row)
    await session.commit()


# ── Read — analyses ───────────────────────────────────────────────────────────

async def get_analyses(session: AsyncSession) -> list[Analysis]:
    result = await session.execute(
        select(Analysis).order_by(Analysis.generated_at.desc())
    )
    return list(result.scalars().all())


async def get_analysis_by_id(session: AsyncSession, analysis_id: str) -> Analysis | None:
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    return result.scalar_one_or_none()


async def get_log_results(session: AsyncSession, analysis_id: str) -> list[LogResult]:
    result = await session.execute(
        select(LogResult)
        .where(LogResult.analysis_id == analysis_id)
        .order_by(LogResult.line_index)
    )
    return list(result.scalars().all())


async def get_csv_path(session: AsyncSession, analysis_id: str) -> str | None:
    analysis = await get_analysis_by_id(session, analysis_id)
    if analysis:
        return analysis.csv_path
    return None


# ── Read — live events ────────────────────────────────────────────────────────

async def get_live_events(
    session: AsyncSession,
    live_session_id: str,
    limit: int = 50,
    label: str | None = None,
) -> list[LogResult]:
    q = (
        select(LogResult)
        .where(LogResult.analysis_id == live_session_id)
        .order_by(LogResult.created_at.desc())
        .limit(limit)
    )
    if label and label != "all":
        q = q.where(LogResult.label == label)
    result = await session.execute(q)
    return list(result.scalars().all())


# ── Read — dashboard aggregates ───────────────────────────────────────────────

async def get_dashboard_summary(session: AsyncSession) -> dict:
    # Total analyses
    total_analyses_r = await session.execute(select(func.count()).select_from(Analysis))
    total_analyses = total_analyses_r.scalar() or 0

    # Total logs
    total_logs_r = await session.execute(select(func.sum(Analysis.total_logs)).select_from(Analysis))
    total_logs = int(total_logs_r.scalar() or 0)

    # Label counts from log_results
    label_rows = await session.execute(
        select(LogResult.label, func.count().label("cnt"))
        .group_by(LogResult.label)
    )
    label_counts = {"malicious": 0, "suspicious": 0, "benign": 0}
    for row in label_rows:
        if row.label in label_counts:
            label_counts[row.label] = row.cnt

    # Severity counts
    severity_rows = await session.execute(
        select(LogResult.severity, func.count().label("cnt"))
        .group_by(LogResult.severity)
    )
    severity_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for row in severity_rows:
        key = row.severity if row.severity in severity_counts else "unknown"
        severity_counts[key] += row.cnt

    # Average times from analyses table
    avg_r = await session.execute(
        select(
            func.avg(Analysis.avg_classification_time_sec),
            func.avg(Analysis.avg_analysis_generation_time_sec),
            func.avg(Analysis.avg_total_time_sec),
        ).select_from(Analysis)
    )
    avg_row = avg_r.one()
    avg_classification = round(float(avg_row[0] or 0), 3)
    avg_analysis = round(float(avg_row[1] or 0), 3)
    avg_total = round(float(avg_row[2] or 0), 3)

    # Recent critical (malicious) events
    critical_r = await session.execute(
        select(LogResult)
        .where(LogResult.label == "malicious")
        .order_by(LogResult.created_at.desc())
        .limit(10)
    )
    critical_events = [
        {
            "log": r.log_text,
            "label": r.label,
            "severity": r.severity,
            "status": r.status,
            "explanation": r.explanation or "",
            "recommendation": r.recommendation or "",
            "created_at": r.created_at,
            "analysis_id": r.analysis_id,
        }
        for r in critical_r.scalars().all()
    ]

    # Recent analyses
    recent_r = await session.execute(
        select(Analysis).order_by(Analysis.generated_at.desc()).limit(10)
    )
    recent_analyses = [
        {
            "analysis_id": a.id,
            "source_name": a.source_name,
            "source_type": a.source_type,
            "analysis_mode": a.analysis_mode,
            "total_logs": a.total_logs,
            "malicious_count": a.malicious_count,
            "suspicious_count": a.suspicious_count,
            "benign_count": a.benign_count,
            "generated_at": a.generated_at,
            "csv_download_url": f"/api/results/{a.id}/download",
        }
        for a in recent_r.scalars().all()
    ]

    return {
        "total_analyses": total_analyses,
        "total_logs": total_logs,
        "label_counts": label_counts,
        "severity_counts": severity_counts,
        "avg_classification_time_sec": avg_classification,
        "avg_analysis_generation_time_sec": avg_analysis,
        "avg_total_time_sec": avg_total,
        "recent_critical_events": critical_events,
        "recent_analyses": recent_analyses,
    }
