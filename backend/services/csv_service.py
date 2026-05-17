"""
Saves analysis results as CSV.
Filenames are unique; existing files are never overwritten.
"""
import csv
import re
import logging
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

COLUMNS = [
    "index",
    "log",
    "label",
    "severity",
    "status",
    "analysis_mode",
    "classification_time_sec",
    "explanation_time_sec",
    "recommendation_time_sec",
    "analysis_generation_time_sec",
    "total_time_sec",
    "raw_classification",
    "explanation",
    "recommendation",
    "simulated_action",
]


def _safe_name(name: str) -> str:
    """Strip unsafe characters from a filename component."""
    name = re.sub(r"[^\w\-.]", "_", name)
    return name[:60]


def save_results_csv(
    results: list[dict],
    source_name: str,
    analysis_id: str,
) -> Path:
    safe = _safe_name(source_name)
    short_id = analysis_id[:8]
    filename = f"{safe}_{short_id}.csv"
    out_dir = settings.results_dir_abs
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / filename

    # Never overwrite
    counter = 1
    while dest.exists():
        dest = out_dir / f"{safe}_{short_id}_{counter}.csv"
        counter += 1

    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    logger.info("CSV saved: %s", dest)
    return dest
