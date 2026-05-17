"""
Core pipeline service.
Refactored from v2.0/analyze_log_pipeline.py.

GPU inference is blocking — callers must use asyncio.to_thread().
Model singletons are imported from model_loader; never re-loaded here.
"""
import re
import time
import csv
import io
import logging
from pathlib import Path

import torch

from backend.config import settings
from backend.schemas.analysis import SEVERITY_MAP, SIMULATED_ACTION_MAP
import backend.services.model_loader as ml

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_label(text: str) -> str | None:
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)|\b(benign|suspicious|malicious)\b",
        text,
        re.I,
    )
    if not match:
        return None
    return (match.group(1) or match.group(2)).lower()


def clean_after_response(full_text: str) -> str:
    if "### Response:" in full_text:
        return full_text.split("### Response:")[-1].strip()
    return full_text.strip()


def normalize_explanation(text: str) -> str:
    text = text.strip()
    if "Recommendation:" in text:
        text = text.split("Recommendation:")[0].strip()
    if "Explanation:" in text:
        text = text.split("Explanation:", 1)[-1].strip()
    return "Explanation: " + text.strip()


def normalize_recommendation(text: str) -> str:
    text = text.strip()
    if "Recommendation:" in text:
        text = text.split("Recommendation:", 1)[-1].strip()
    if "Explanation:" in text:
        text = text.split("Explanation:")[0].strip()
    return "Recommendation: " + text.strip()


def detect_log_context(log_entry: str) -> str:
    log_lower = log_entry.lower()
    cowrie = ["cmd:", "login attempt", "remote ssh version", "closing tty log",
              "authorized_keys", "chpasswd", "wget", "curl", "busybox", "session", "tty"]
    hdfs = ["dfs.", "datanode", "fsnamesystem", "packetresponder",
            "dataxceiver", "block", "blk_"]
    if any(k in log_lower for k in cowrie):
        return "cowrie_honeypot"
    if any(k in log_lower for k in hdfs):
        return "hdfs"
    return "generic"


def _context_note(context: str, mode: str = "explanation") -> str:
    if context == "cowrie_honeypot":
        if mode == "explanation":
            return (
                "Context: This log comes from a Cowrie honeypot environment. "
                "SSH activity, command execution, login attempts, TTY session events, "
                "and client fingerprints should be interpreted as attacker activity. "
                "Do not describe the event as potentially legitimate."
            )
        return (
            "Context: Cowrie honeypot. Recommended actions should focus on "
            "source IP correlation, session reconstruction, command analysis, "
            "downloaded files, credentials used, and IOC extraction."
        )
    if context == "hdfs":
        if mode == "explanation":
            return (
                "Context: This log comes from an HDFS environment. "
                "Normal block transfer, addStoredBlock, PacketResponder, and DataXceiver events "
                "may be benign unless there is explicit anomaly context."
            )
        return (
            "Context: HDFS log. Recommended actions should focus on block ID correlation, "
            "related events, anomaly history, and DataNode/NameNode behavior."
        )
    if mode == "explanation":
        return (
            "Context: This is a generic cybersecurity log. "
            "Base the explanation only on the observable behavior in the log."
        )
    return "Context: Generic cybersecurity log. Recommend one concrete investigation or mitigation step."


# ── Core generation ───────────────────────────────────────────────────────────

def _generate(prompt: str, adapter_name: str, max_new_tokens: int, max_length: int = 512):
    ml.model.set_adapter(adapter_name)
    inputs = ml.tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    ).to(ml.model.device)

    t0 = time.time()
    with torch.no_grad():
        outputs = ml.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=ml.tokenizer.eos_token_id,
        )
    elapsed = time.time() - t0

    full_text = ml.tokenizer.decode(outputs[0], skip_special_tokens=True)
    answer = clean_after_response(full_text)
    return answer, elapsed


# ── LLM-A ─────────────────────────────────────────────────────────────────────

def classify_log(log_entry: str) -> tuple[str | None, str, float]:
    prompt = (
        "### Instruction:\n"
        "Classify the following cybersecurity log entry using only one label: "
        "benign, suspicious, or malicious.\n"
        "Return only the label in this format: Label: <label>.\n\n"
        f"### Input:\n{log_entry}\n\n"
        "### Response:\n"
    )
    answer, elapsed = _generate(
        prompt, "classifier",
        max_new_tokens=settings.MAX_NEW_TOKENS_CLASSIFICATION,
        max_length=256,
    )
    label = extract_label(answer)
    return label, answer, elapsed


# ── LLM-B ─────────────────────────────────────────────────────────────────────

def generate_explanation(log_entry: str, label: str) -> tuple[str, float]:
    context = detect_log_context(log_entry)
    ctx_note = _context_note(context, mode="explanation")
    prompt = (
        "### Instruction:\n"
        "You are a cybersecurity SOC analyst.\n\n"
        f"The following log was classified as {label}.\n\n"
        f"{ctx_note}\n\n"
        "Write one short technical explanation.\n"
        "Rules:\n"
        "- Do not hedge.\n"
        "- Do not say \"legitimate\" if the context is Cowrie honeypot and the label is malicious.\n"
        "- Explain the security meaning of the observed behavior.\n"
        "- Do not write a recommendation.\n"
        "- Return only one Explanation line.\n\n"
        f"### Input:\n{log_entry}\n\n"
        "### Response:\nExplanation:"
    )
    answer, elapsed = _generate(
        prompt, "analysis",
        max_new_tokens=80,
        max_length=512,
    )
    return normalize_explanation(answer), elapsed


# ── LLM-C ─────────────────────────────────────────────────────────────────────

def generate_recommendation(log_entry: str, label: str, explanation: str) -> tuple[str, float]:
    context = detect_log_context(log_entry)
    ctx_note = _context_note(context, mode="recommendation")
    prompt = (
        "### Instruction:\n"
        "You are a cybersecurity SOC analyst.\n\n"
        f"The following log was classified as {label}.\n\n"
        f"{ctx_note}\n\n"
        "Based on the explanation, write one concrete security recommendation.\n"
        "Rules:\n"
        "- Return only one Recommendation line.\n"
        "- Make the action specific and operational.\n"
        "- Do not give generic advice such as only \"monitor activity\".\n"
        "- Do not recommend password resets unless the log clearly involves credential compromise.\n"
        "- Prefer correlation, IOC extraction, session reconstruction, source analysis, or containment.\n\n"
        f"### Input:\nLog:\n{log_entry}\n\n{explanation}\n\n"
        "### Response:\nRecommendation:"
    )
    answer, elapsed = _generate(
        prompt, "analysis",
        max_new_tokens=80,
        max_length=512,
    )
    return normalize_recommendation(answer), elapsed


# ── Combined (LLM-B + LLM-C in one call) ──────────────────────────────────────

def generate_combined_analysis(log_entry: str, label: str) -> tuple[str, str, float]:
    context = detect_log_context(log_entry)

    if context == "cowrie_honeypot":
        ctx_note = (
            "Context: This log comes from a Cowrie honeypot environment. "
            "SSH activity, command execution, login attempts, TTY events, and client fingerprints "
            "should be interpreted as attacker activity. Do not describe the event as legitimate."
        )
    elif context == "hdfs":
        ctx_note = (
            "Context: This log comes from an HDFS environment. "
            "Normal block transfer, addStoredBlock, PacketResponder, and DataXceiver events "
            "may be benign unless there is explicit anomaly context."
        )
    else:
        ctx_note = (
            "Context: This is a generic cybersecurity log. "
            "Base the analysis only on the observable behavior."
        )

    prompt = (
        "### Instruction:\n"
        "You are a cybersecurity SOC analyst.\n\n"
        f"The following log was classified as {label}.\n\n"
        f"{ctx_note}\n\n"
        "Generate exactly two fields:\n"
        "1. Explanation\n"
        "2. Recommendation\n\n"
        "Rules:\n"
        "- Explanation must be short, technical, and direct.\n"
        "- Recommendation must be concrete and operational.\n"
        "- Do not hedge.\n"
        "- Do not say \"legitimate\" for Cowrie honeypot malicious activity.\n"
        "- Do not recommend password resets unless the log clearly involves credential compromise.\n"
        "- Return only these two lines.\n\n"
        f"### Input:\n{log_entry}\n\n"
        "### Response:\nExplanation:"
    )
    answer, elapsed = _generate(
        prompt, "analysis",
        max_new_tokens=settings.MAX_NEW_TOKENS_ANALYSIS,
        max_length=512,
    )
    answer = answer.strip()
    if not answer.lower().startswith("explanation:"):
        answer = "Explanation: " + answer

    if "Recommendation:" in answer:
        explanation_part = answer.split("Recommendation:", 1)[0].strip()
        recommendation_part = answer.split("Recommendation:", 1)[1].strip()
        explanation = normalize_explanation(explanation_part)
        recommendation = "Recommendation: " + recommendation_part.strip()
    else:
        explanation = normalize_explanation(answer)
        recommendation = (
            "Recommendation: Correlate this event with related session activity, "
            "source indicators, and neighboring logs for incident validation."
        )

    return explanation, recommendation, elapsed


# ── Single log analysis ───────────────────────────────────────────────────────

def analyze_single_log(log_entry: str, analysis_mode: str) -> dict:
    label, raw_classification, classification_time = classify_log(log_entry)

    explanation = ""
    recommendation = ""
    explanation_time = 0.0
    recommendation_time = 0.0
    status = ""

    if label == "benign":
        status = "no_action"
        recommendation = "Recommendation: No action required."

    elif label == "malicious":
        status = f"analysis_generated_{analysis_mode}"

        if analysis_mode == "combined":
            explanation, recommendation, combined_time = generate_combined_analysis(
                log_entry=log_entry, label=label
            )
            explanation_time = combined_time
            recommendation_time = 0.0

        elif analysis_mode == "separate":
            explanation, explanation_time = generate_explanation(log_entry=log_entry, label=label)
            recommendation, recommendation_time = generate_recommendation(
                log_entry=log_entry, label=label, explanation=explanation
            )

        else:
            status = "invalid_analysis_mode"
            explanation = "Explanation: Invalid analysis mode selected."
            recommendation = "Recommendation: Use either combined or separate mode."

    elif label == "suspicious":
        status = "context_required"
        explanation = (
            "Explanation: The log was classified as suspicious, but this category "
            "may require block-level or session-level correlation before escalation."
        )
        recommendation = (
            "Recommendation: Correlate this event with related block IDs, session IDs, "
            "neighboring events, and anomaly history before taking action."
        )

    else:
        status = "label_not_extracted"
        explanation = "Explanation: The model output could not be parsed into a valid label."
        recommendation = "Recommendation: Review the log manually."

    analysis_generation_time = explanation_time + recommendation_time
    total_time = classification_time + analysis_generation_time
    severity = SEVERITY_MAP.get(label or "unknown", "unknown")
    simulated_action = SIMULATED_ACTION_MAP.get(label or "benign")

    return {
        "log": log_entry,
        "label": label or "unknown",
        "status": status,
        "severity": severity,
        "analysis_mode": analysis_mode,
        "classification_time_sec": round(classification_time, 3),
        "explanation_time_sec": round(explanation_time, 3),
        "recommendation_time_sec": round(recommendation_time, 3),
        "analysis_generation_time_sec": round(analysis_generation_time, 3),
        "total_time_sec": round(total_time, 3),
        "raw_classification": raw_classification or "",
        "explanation": explanation,
        "recommendation": recommendation,
        "simulated_action": simulated_action,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_logs(lines: list[str], analysis_mode: str) -> list[dict]:
    """Analyze a list of log lines. Blocking — wrap with asyncio.to_thread."""
    if not ml.model_loaded:
        raise RuntimeError(ml.model_error or "Model is not loaded.")

    results = []
    for i, line in enumerate(lines):
        logger.info("Analyzing log %d/%d", i + 1, len(lines))
        result = analyze_single_log(line, analysis_mode)
        result["index"] = i
        results.append(result)

    return results


def load_logs_from_text(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def parse_uploaded_file(file_path: str) -> list[str]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        import pandas as pd
        df = pd.read_csv(path, dtype=str)
        for col in ("log", "message", "raw_log"):
            if col in df.columns:
                return [str(v).strip() for v in df[col].dropna() if str(v).strip()]
        # Fallback: all non-empty rows joined as strings
        lines = []
        for _, row in df.iterrows():
            merged = " ".join(str(v) for v in row.values if str(v).strip() not in ("", "nan"))
            if merged.strip():
                lines.append(merged.strip())
        return lines

    # .txt / .log
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]
