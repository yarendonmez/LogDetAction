import json
import re
from pathlib import Path

import pandas as pd


input_path = Path(r"C:\developer\LogDetAction\v2.0\training_dataset.csv")
output_path = Path(r"C:\developer\LogDetAction\v2.0\llm_instruction_dataset_advanced.jsonl")

MAX_ROWS = None  # Hepsini üretmek için None bırak.


def get_cowrie_reason(source: str, message: str) -> tuple[str, str]:
    source = str(source).lower()
    message = str(message).lower()

    if "login.failed" in source:
        return (
            "Failed SSH authentication was detected. This behavior is commonly associated with brute-force or credential guessing attempts against remote access services.",
            "Review the source IP, apply rate limiting, and block repeated failed login attempts if necessary."
        )

    if "login.success" in source:
        return (
            "A successful SSH login was observed in the honeypot environment. Since honeypots should not receive legitimate access, this may indicate unauthorized access or compromised credentials.",
            "Investigate the session activity, preserve logs, and monitor commands executed after login."
        )

    if "command.input" in source:
        return (
            "An attacker issued shell commands inside the honeypot session. Interactive command execution indicates post-login activity and may reveal reconnaissance, persistence, or malware deployment behavior.",
            "Analyze the executed command, extract indicators of compromise, and check whether similar commands appear in other sessions."
        )

    if "file_download" in source:
        return (
            "A file download attempt was observed during the SSH session. Attackers often download malware, scripts, or tools after gaining access to a system.",
            "Inspect the downloaded file URL or hash, block malicious sources, and isolate affected hosts if similar activity appears in production."
        )

    if "session.connect" in source:
        return (
            "A remote SSH connection attempt was initiated against the honeypot. This indicates external scanning or attempted unauthorized access.",
            "Monitor connection frequency from the source IP and correlate it with authentication attempts."
        )

    if "session.closed" in source or "log.closed" in source:
        return (
            "An SSH session was closed after previous interaction with the honeypot. Session closure alone is not the attack, but it provides context for the attacker activity timeline.",
            "Correlate this session with login attempts, commands, and file downloads from the same source."
        )

    if "client.version" in source or "client.kex" in source:
        return (
            "SSH client version or key exchange information was recorded. This can help fingerprint the attacking tool or client used during the connection attempt.",
            "Use the client fingerprint for correlation and threat intelligence enrichment."
        )

    if "direct-tcpip" in source:
        return (
            "A direct TCP forwarding request was observed. This may indicate tunneling, proxying, or lateral movement behavior attempted through SSH.",
            "Investigate the destination endpoint and block unauthorized tunneling behavior."
        )

    return (
        "The honeypot recorded activity consistent with unauthorized SSH probing or attacker interaction.",
        "Correlate the event with source IP, session history, login attempts, and executed commands."
    )


def get_hdfs_reason(label: str, message: str) -> tuple[str, str]:
    msg = str(message).lower()

    if label == "suspicious":
        if "error" in msg or "exception" in msg or "failed" in msg:
            return (
                "The HDFS log contains failure or error-related behavior associated with an anomalous block operation. This may indicate node instability, block corruption, or abnormal distributed file system activity.",
                "Check the related block ID, inspect DataNode health, and verify whether similar failures occur within the same time window."
            )

        if "blk_" in msg:
            return (
                "The HDFS log belongs to a block operation marked as anomalous by the ground-truth label. Abnormal block behavior may indicate data corruption, replication issues, or node communication problems.",
                "Investigate the affected block ID, validate replication status, and review nearby logs from the same host."
            )

        return (
            "The HDFS event is labeled as anomalous and may indicate abnormal system behavior in the distributed storage environment.",
            "Review related events, node status, and block-level activity for root-cause analysis."
        )

    return (
        "The HDFS log represents normal distributed file system activity and does not show indicators of anomalous or malicious behavior.",
        "No immediate action is required; retain the event for baseline monitoring and future correlation."
    )


def build_output(row: pd.Series) -> str:
    label = str(row.get("label", "")).strip()
    dataset = str(row.get("dataset", "")).strip()
    source = str(row.get("source", "")).strip()
    message = str(row.get("message", "")).strip()

    if dataset.lower() == "cowrie":
        explanation, recommendation = get_cowrie_reason(source, message)
    else:
        explanation, recommendation = get_hdfs_reason(label, message)

    return (
        f"Label: {label}\n"
        f"Explanation: {explanation}\n"
        f"Recommendation: {recommendation}"
    )


def clean_input(text: str) -> str:
    text = str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


df = pd.read_csv(input_path)

if MAX_ROWS is not None:
    df = df.head(MAX_ROWS)

instruction = (
    "Analyze the following cybersecurity log entry. "
    "Classify it as benign, suspicious, or malicious. "
    "Then provide a short technical explanation and one recommended action."
)

count = 0

with open(output_path, "w", encoding="utf-8") as f:
    for _, row in df.iterrows():
        item = {
            "instruction": instruction,
            "input": clean_input(row.get("message", "")),
            "output": build_output(row)
        }

        f.write(json.dumps(item, ensure_ascii=False) + "\n")
        count += 1

print("Tamamlandı.")
print("Çıktı:", output_path)
print("Toplam örnek:", count)

print("\nLabel dağılımı:")
print(df["label"].value_counts())

print("\nDataset dağılımı:")
print(df["dataset"].value_counts())