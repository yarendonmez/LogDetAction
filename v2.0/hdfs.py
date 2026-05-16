import pandas as pd
import re
from pathlib import Path

hdfs_log_path = Path(r"C:\developer\LogDetAction\v2.0\HDFS_v1\HDFS.log")
label_path = Path(r"C:\developer\LogDetAction\v2.0\HDFS_v1\preprocessed\anomaly_label.csv")
output_path = Path(r"C:\developer\LogDetAction\v2.0\HDFS_processed.csv")

MAX_LINES = 100_000

labels = pd.read_csv(label_path)
labels.columns = [c.strip() for c in labels.columns]

label_map = dict(zip(labels["BlockId"], labels["Label"]))

def extract_block_id(line):
    match = re.search(r"blk_-?\d+", line)
    return match.group(0) if match else None

rows = []

with open(hdfs_log_path, "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        if i >= MAX_LINES:
            break

        raw = line.strip()
        block_id = extract_block_id(raw)

        original_label = label_map.get(block_id, "Unknown")

        if original_label == "Normal":
            label = "benign"
        elif original_label == "Anomaly":
            label = "suspicious"
        else:
            label = "unknown"

        rows.append({
            "timestamp": None,
            "source": "HDFS",
            "message": raw,
            "raw_message": raw,
            "block_id": block_id,
            "original_label": original_label,
            "label": label,
            "dataset": "HDFS"
        })

df = pd.DataFrame(rows)

df = df[df["label"] != "unknown"]

df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("Tamamlandı.")
print("Çıktı:", output_path)
print("Satır sayısı:", len(df))
print(df["label"].value_counts())