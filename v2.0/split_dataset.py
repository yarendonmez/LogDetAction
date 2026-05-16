import json
import random
from pathlib import Path

input_path = Path(r"C:\developer\LogDetAction\v2.0\llm_instruction_dataset_advanced.jsonl")
output_dir = Path(r"C:\developer\LogDetAction\v2.0\split")
output_dir.mkdir(exist_ok=True)

train_path = output_dir / "train.jsonl"
val_path = output_dir / "validation.jsonl"
test_path = output_dir / "test.jsonl"

random.seed(42)

with open(input_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

random.shuffle(lines)

total = len(lines)
train_end = int(total * 0.8)
val_end = int(total * 0.9)

splits = {
    train_path: lines[:train_end],
    val_path: lines[train_end:val_end],
    test_path: lines[val_end:]
}

for path, split_lines in splits.items():
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(split_lines)

print("Tamamlandı.")
print("Toplam:", total)
print("Train:", len(splits[train_path]))
print("Validation:", len(splits[val_path]))
print("Test:", len(splits[test_path]))
print("Çıktı klasörü:", output_dir)
