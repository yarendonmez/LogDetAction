"""
test.jsonl dosyasından dengeli (her label eşit) log test dosyaları üretir.

Çıktı: v2.0/data/splits/ klasörüne .txt dosyaları (sadece log satırları)
Boyutlar: 10, 50, 100, 200, 500

Her dosyada label'lar mümkün olduğunca eşit dağılır.
Örn: 100-satırlık dosya → ~33 benign, ~33 suspicious, ~33 malicious (kalan 1 fazla benign'a gider)
"""

import json
import random
from collections import defaultdict
from pathlib import Path

RANDOM_SEED = 42
INPUT_FILE = Path(__file__).parent / "split" / "test.jsonl"
OUTPUT_DIR = Path(__file__).parent / "data" / "splits"
SIZES = [10, 50, 100, 200, 500]

random.seed(RANDOM_SEED)


def load_by_label(path: Path) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            log_text = obj.get("input", "").strip()
            output = obj.get("output", "")
            # label'ı output'tan çıkar
            label = None
            for part in output.split("\n"):
                part = part.strip()
                if part.lower().startswith("label:"):
                    label = part.split(":", 1)[1].strip().lower()
                    break
            if log_text and label in ("benign", "suspicious", "malicious"):
                buckets[label].append(log_text)
    return dict(buckets)


def make_balanced_sample(buckets: dict[str, list[str]], total: int) -> list[str]:
    labels = list(buckets.keys())
    n_labels = len(labels)
    base = total // n_labels
    extra = total % n_labels  # kalan satırlar ilk label'a gider

    selected: list[str] = []
    for i, label in enumerate(sorted(labels)):  # sıralı: benign, malicious, suspicious
        count = base + (1 if i < extra else 0)
        pool = buckets[label]
        chosen = random.sample(pool, min(count, len(pool)))
        selected.extend(chosen)

    random.shuffle(selected)
    return selected


def main():
    print(f"Kaynak: {INPUT_FILE}")
    buckets = load_by_label(INPUT_FILE)

    for label, items in sorted(buckets.items()):
        print(f"  {label}: {len(items)} log")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for size in SIZES:
        sample = make_balanced_sample(buckets, size)
        out_path = OUTPUT_DIR / f"test_balanced_{size}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sample) + "\n")
        print(f"\n[{size}] -> {out_path.name}")

        # Dağılımı doğrula (her satır hangi bucket'tan geldi bilemeyiz ama sayı doğru)
        print(f"  Toplam satır: {len(sample)}")


if __name__ == "__main__":
    main()
