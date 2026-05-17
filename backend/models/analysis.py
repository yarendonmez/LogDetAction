from datetime import datetime, timezone
from sqlalchemy import Integer, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_mode: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[str] = mapped_column(Text, nullable=False)
    total_logs: Mapped[int] = mapped_column(Integer, nullable=False)
    malicious_count: Mapped[int] = mapped_column(Integer, nullable=False)
    suspicious_count: Mapped[int] = mapped_column(Integer, nullable=False)
    benign_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_classification_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    avg_analysis_generation_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    avg_total_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    csv_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    log_results: Mapped[list["LogResult"]] = relationship(
        "LogResult", back_populates="analysis", cascade="all, delete-orphan"
    )


class LogResult(Base):
    __tablename__ = "log_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(Text, ForeignKey("analyses.id"), nullable=False)
    line_index: Mapped[int] = mapped_column(Integer, nullable=False)
    log_text: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_mode: Mapped[str] = mapped_column(Text, nullable=False)
    classification_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    analysis_generation_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    total_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    raw_classification: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    simulated_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="log_results")
