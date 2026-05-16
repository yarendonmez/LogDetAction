import json
import random
import re
from pathlib import Path
from collections import defaultdict, Counter

base_dir = Path(r"C:\developer\LogDetAction\v2.0")

input_path = base_dir / "split_classifier" / "train.jsonl"
output_path = base_dir / "split_classifier" / "train_balanced_3000.jsonl"

RANDOM_SEED = 42
SAMPLES_PER_CLASS = 1000

LABELS = ["benign", "suspicious", "malicious"]


def extract_label(text):
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)",
        text,
        re.I
    )
    return match.group(1).lower() if match else None


items_by_label = defaultdict(list)

with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        label = extract_label(item["output"])

        if label in LABELS:
            items_by_label[label].append(item)


print("Train set label dağılımı:")
for label in LABELS:
    print(label, len(items_by_label[label]))


random.seed(RANDOM_SEED)

balanced_items = []

for label in LABELS:
    available = len(items_by_label[label])
    sample_count = min(SAMPLES_PER_CLASS, available)

    selected = random.sample(items_by_label[label], sample_count)
    balanced_items.extend(selected)

    print(f"Seçilen {label}: {sample_count}/{available}")


random.shuffle(balanced_items)

with open(output_path, "w", encoding="utf-8") as f:
    for item in balanced_items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


final_dist = Counter(extract_label(item["output"]) for item in balanced_items)

print("\nBalanced dataset oluşturuldu.")
print("Çıktı:", output_path)
print("Toplam örnek:", len(balanced_items))
print("Final dağılım:", dict(final_dist))