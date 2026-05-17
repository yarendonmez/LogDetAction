from __future__ import annotations
from pydantic import BaseModel


SEVERITY_MAP = {
    "malicious": "high",
    "suspicious": "medium",
    "benign": "low",
}

SIMULATED_ACTION_MAP = {
    "malicious": (
        "Pending analyst approval: investigate source, session timeline, and related indicators."
    ),
    "suspicious": (
        "Pending analyst review: correlate with neighboring logs and context before escalation."
    ),
    "benign": None,
}


class LogResult(BaseModel):
    index: int
    log: str
    label: str
    status: str
    severity: str
    analysis_mode: str
    classification_time_sec: float
    explanation_time_sec: float
    recommendation_time_sec: float
    analysis_generation_time_sec: float
    total_time_sec: float
    raw_classification: str
    explanation: str
    recommendation: str
    simulated_action: str | None = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    source_type: str
    source_name: str
    analysis_mode: str
    generated_at: str
    total_logs: int
    malicious_count: int
    suspicious_count: int
    benign_count: int
    avg_classification_time_sec: float
    avg_analysis_generation_time_sec: float
    avg_total_time_sec: float
    csv_download_url: str
    results: list[LogResult]


class AnalysisSummary(BaseModel):
    analysis_id: str
    source_type: str
    source_name: str
    analysis_mode: str
    generated_at: str
    total_logs: int
    malicious_count: int
    suspicious_count: int
    benign_count: int
    avg_total_time_sec: float
    csv_download_url: str


class TextAnalysisRequest(BaseModel):
    text: str
    analysis_mode: str = "combined"


class ErrorResponse(BaseModel):
    error: bool = True
    code: str
    message: str
