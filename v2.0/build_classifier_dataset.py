import json
import re
from pathlib import Path

base_dir = Path(r"C:\developer\LogDetAction\v2.0")

input_split_dir = base_dir / "split"
output_split_dir = base_dir / "split_classifier"
output_split_dir.mkdir(exist_ok=True)

files = {
    "train": input_split_dir / "train.jsonl",
    "validation": input_split_dir / "validation.jsonl",
    "test": input_split_dir / "test.jsonl",
}

def extract_label(output_text):
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)",
        output_text,
        re.I
    )
    if not match:
        return None
    return match.group(1).lower()

instruction = (
    "Classify the following cybersecurity log entry using only one label: "
    "benign, suspicious, or malicious. Return only the label in this format: Label: <label>."
)

for split_name, input_path in files.items():
    output_path = output_split_dir / f"{split_name}.jsonl"

    count = 0
    skipped = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            item = json.loads(line)

            label = extract_label(item["output"])

            if label is None:
                skipped += 1
                continue

            new_item = {
                "instruction": instruction,
                "input": item["input"],
                "output": f"Label: {label}"
            }

            fout.write(json.dumps(new_item, ensure_ascii=False) + "\n")
            count += 1

    print(f"{split_name} tamamlandı.")
    print("Çıktı:", output_path)
    print("Yazılan:", count)
    print("Atlanan:", skipped)
    print()