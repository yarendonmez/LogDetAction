import pandas as pd
import json
from pathlib import Path

input_path = Path(r"C:\developer\LogDetAction\v2.0\training_dataset.csv")
output_path = Path(r"C:\developer\LogDetAction\v2.0\llm_instruction_dataset.jsonl")

df = pd.read_csv(input_path)

instruction = "Analyze the following cybersecurity log entry and classify it."

output_lines = []

for _, row in df.iterrows():

    log_message = str(row["message"])
    label = str(row["label"])

    if label == "malicious":
        explanation = "This log indicates malicious or attacker behavior."
    elif label == "suspicious":
        explanation = "This log indicates anomalous or suspicious system behavior."
    else:
        explanation = "This log appears to represent normal benign system activity."

    output_text = f"Label: {label}. Explanation: {explanation}"

    item = {
        "instruction": instruction,
        "input": log_message,
        "output": output_text
    }

    output_lines.append(item)

with open(output_path, "w", encoding="utf-8") as f:
    for item in output_lines:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Tamamlandı.")
print("Çıktı:", output_path)
print("Toplam örnek:", len(output_lines))