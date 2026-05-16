import json
from pathlib import Path
import pandas as pd

cowrie_dir = Path(r"C:\developer\LogDetAction\v2.0\cowrie")
output_path = Path(r"C:\developer\LogDetAction\v2.0\Cowrie_processed.csv")

MAX_LOGS = 100_000

rows = []

files = sorted(cowrie_dir.glob("cowrie.json.*"))

for file_path in files:
    print("Okunuyor:", file_path.name)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if len(rows) >= MAX_LOGS:
                break

            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            eventid = record.get("eventid", "")
            timestamp = record.get("timestamp", "")
            src_ip = record.get("src_ip", "")
            username = record.get("username", "")
            message = record.get("message", "")

            if not message:
                message = f"{eventid} src_ip={src_ip} username={username}"

            rows.append({
                "timestamp": timestamp,
                "source": eventid,
                "message": message,
                "raw_message": line,
                "block_id": None,
                "original_label": "Attack",
                "label": "malicious",
                "dataset": "Cowrie"
            })

    if len(rows) >= MAX_LOGS:
        break

df = pd.DataFrame(rows)
df.to_csv(output_path, index=False, encoding="utf-8-sig", escapechar="\\")

print("Tamamlandı.")
print("Çıktı:", output_path)
print("Satır sayısı:", len(df))
print(df["label"].value_counts())
print("Event dağılımı:")
print(df["source"].value_counts().head(15))